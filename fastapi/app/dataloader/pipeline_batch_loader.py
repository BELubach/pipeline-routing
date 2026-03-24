"""
Batch loader for GEM pipeline data with progress tracking.
Processes large GeoJSON files segment-by-segment with error handling.
"""
import logging
from typing import Optional, Dict, Any
from datetime import datetime
from pathlib import Path

import geopandas as gpd
import pandas as pd
from shapely.geometry import LineString
from sqlalchemy import text
from sqlalchemy.orm import Session
from geoalchemy2.shape import from_shape

from app.models.pipeline import PipelineNode, PipelineEdge
from app.models.pipeline_import import PipelineImportJob, PipelineImportSegment, PipelineImportChunk

logger = logging.getLogger(__name__)


class PipelineBatchLoader:
    """
    Spring Batch-style loader for pipeline GeoJSON data.
    Handles large files with progress tracking and resume capability.
    """
    
    # GEM status mapping
    GEM_STATUS_MAP = {
        "Operating": "operating",
        "Construction": "construction",
        "Pre-construction": "planned",
        "Proposed": "planned",
        "Announced": "planned",
        "Cancelled": "decommissioned",
        "Shelved": "decommissioned",
        "Retired": "decommissioned",
        "Idle": "decommissioned",
    }
    
    def __init__(self, db: Session):
        self.db = db
        self.current_job: Optional[PipelineImportJob] = None
    
    def load_file(
        self,
        geojson_path: str,
        batch_size: int = 100,
        europe_only: bool = True,
        existing_job: Optional[PipelineImportJob] = None
    ) -> PipelineImportJob:
        """
        Load pipeline data from GeoJSON file with batch processing.
        
        Args:
            geojson_path: Path to GEM pipeline GeoJSON file
            batch_size: Number of segments to commit per batch
            europe_only: Filter to Europe bounding box
            
        Returns:
            PipelineImportJob with final status
        """
        filepath = Path(geojson_path)
        if not filepath.exists():
            raise FileNotFoundError(f"GeoJSON file not found: {geojson_path}")

        logger.info(f"Starting pipeline import from {filepath.name}")

        # Use existing job if resuming, else create new
        if existing_job is not None:
            job = existing_job
        else:
            job = PipelineImportJob(
                filename=filepath.name,
                status='running'
            )
            self.db.add(job)
            self.db.commit()
            self.db.refresh(job)
        self.current_job = job
        
        try:
            # Load GeoJSON
            logger.info("Reading GeoJSON file...")
            gdf = gpd.read_file(geojson_path)
            gdf = gdf.to_crs(epsg=4326)

            job.total_features = len(gdf)
            self.db.commit()

            if europe_only:
                # Filter to Europe bbox: (lon_min, lat_min, lon_max, lat_max)
                europe_bbox = (-30, 20, 60, 75)
                gdf = gdf.cx[europe_bbox[0]:europe_bbox[2], europe_bbox[1]:europe_bbox[3]]
                logger.info(f"Filtered to Europe bbox: {len(gdf)} features")

            # Explode MultiLineStrings to individual segments
            logger.info("Exploding MultiLineStrings...")
            gdf = gdf.explode(index_parts=False).reset_index(drop=True)
            gdf = gdf[gdf.geometry.geom_type == "LineString"].copy()

            job.total_segments = len(gdf)
            self.db.commit()

            logger.info(f"Processing {len(gdf)} segments in chunks of {batch_size}...")

            total_segments = len(gdf)
            processed = 0
            success_count = 0
            failed_count = 0

            # Find all completed chunks for this job
            completed_chunks = set(
                c.chunk_index for c in self.db.query(PipelineImportChunk)
                .filter(PipelineImportChunk.job_id == job.id, PipelineImportChunk.status == 'success')
            )

            num_chunks = (total_segments + batch_size - 1) // batch_size
            for chunk_idx in range(num_chunks):
                if chunk_idx in completed_chunks:
                    processed += min(batch_size, total_segments - chunk_idx * batch_size)
                    continue  # Skip completed chunk

                start_idx = chunk_idx * batch_size
                end_idx = min(start_idx + batch_size, total_segments)

                # Get or create chunk record
                chunk = self.db.query(PipelineImportChunk).filter_by(job_id=job.id, chunk_index=chunk_idx).first()
                if not chunk:
                    chunk = PipelineImportChunk(
                        job_id=job.id,
                        chunk_index=chunk_idx,
                        start_segment_index=start_idx,
                        end_segment_index=end_idx - 1,
                        status='pending'
                    )
                    self.db.add(chunk)
                    self.db.commit()
                    self.db.refresh(chunk)

                chunk.status = 'running'
                self.db.commit()

                chunk_success = 0
                chunk_failed = 0

                for idx in range(start_idx, end_idx):
                    row = gdf.iloc[idx]
                    # Only check per-segment status within this chunk
                    existing = self.db.query(PipelineImportSegment).filter(
                        PipelineImportSegment.job_id == job.id,
                        PipelineImportSegment.segment_index == int(idx),
                        PipelineImportSegment.status.in_(['success', 'failed', 'skipped'])
                    ).first()
                    if existing:
                        continue

                    segment_record = None
                    try:
                        segment_record = PipelineImportSegment(
                            job_id=job.id,
                            gem_id=self._safe_str(row.get("GEM Unit ID")),
                            pipeline_name=self._safe_str(row.get("Pipeline Name")),
                            segment_index=int(idx),
                            status='pending'
                        )
                        self.db.add(segment_record)

                        edge_id, source_id, target_id = self._process_segment(row)

                        segment_record.status = 'success'
                        segment_record.edge_id = edge_id
                        segment_record.source_node_id = source_id
                        segment_record.target_node_id = target_id
                        chunk_success += 1
                        success_count += 1

                    except Exception as e:
                        logger.error(f"Failed to process segment {idx}: {e}")
                        self.db.rollback()
                        segment_record = PipelineImportSegment(
                            job_id=job.id,
                            gem_id=self._safe_str(row.get("GEM Unit ID")),
                            pipeline_name=self._safe_str(row.get("Pipeline Name")),
                            segment_index=int(idx),
                            status='failed',
                            error_message=str(e)[:1000]
                        )
                        self.db.add(segment_record)
                        chunk_failed += 1
                        failed_count += 1

                processed += (end_idx - start_idx)
                # Mark chunk as success/failed
                if chunk_failed == 0:
                    chunk.status = 'success'
                else:
                    chunk.status = 'failed'
                    chunk.error_message = f"{chunk_failed} failed in chunk {chunk_idx}"
                chunk.processed_at = datetime.utcnow()
                self.db.commit()

                job.processed_segments = processed
                job.successful_segments = success_count
                job.failed_segments = failed_count
                self.db.commit()
                logger.info(f"Chunk {chunk_idx+1}/{num_chunks} done: {chunk_success} success, {chunk_failed} failed. Progress: {processed}/{total_segments}")

            # Final commit
            job.processed_segments = processed
            job.successful_segments = success_count
            job.failed_segments = failed_count
            job.completed_at = datetime.utcnow()
            job.status = 'completed' if failed_count == 0 else 'partial'
            self.db.commit()

            logger.info(f"Import completed: {success_count} successful, {failed_count} failed")
            return job

        except Exception as e:
            logger.error(f"Import job failed: {e}")
            job.status = 'failed'
            job.error_message = str(e)[:1000]
            job.completed_at = datetime.utcnow()
            self.db.commit()
            raise
    
    def _process_segment(self, row: pd.Series) -> tuple[int, int, int]:
        """
        Process a single pipeline segment: create nodes and edge.
        
        Returns:
            (edge_id, source_node_id, target_node_id)
        """
        geom = row.geometry
        if not isinstance(geom, LineString):
            raise ValueError(f"Expected LineString, got {type(geom)}")
        
        coords = list(geom.coords)
        if len(coords) < 2:
            raise ValueError("LineString must have at least 2 points")
        
        # Get or create source node
        source_lon, source_lat = coords[0]
        source_id = self._get_or_create_node(source_lon, source_lat)
        
        # Get or create target node
        target_lon, target_lat = coords[-1]
        target_id = self._get_or_create_node(target_lon, target_lat)
        
        # Create edge
        edge = PipelineEdge(
            source=source_id,
            target=target_id,
            geom=from_shape(geom, srid=4326),
            pipeline_name=self._safe_str(row.get("Pipeline Name")),
            source_name=self._safe_str(row.get("Segment Name") or row.get("Pipeline Name")),
            operator=self._safe_str(row.get("Operator")),
            status=self._map_status(row.get("Status")),
            diameter_mm=self._safe_int(row.get("Diameter (mm)")),
            capacity_mcm_d=self._safe_float(row.get("Max. Capacity (Mm3/d)")),
            length_km=self._safe_float(row.get("LengthMergedKm")),  # Fixed: use correct field
            year_built=self._safe_int(row.get("Start Year")),
            country_codes=self._parse_countries(row.get("CountriesOrAreas")),  # Fixed: use correct field
            gem_id=self._safe_str(row.get("GEM Unit ID")),
            tariff_type='estimated'
        )
        
        self.db.add(edge)
        self.db.flush()  # Get the edge ID without committing
        
        return edge.id, source_id, target_id
    
    def _get_or_create_node(self, lon: float, lat: float, snap_distance_m: float = 500) -> int:
        """
        Get existing node within snap_distance or create new one.
        
        Args:
            lon: Longitude
            lat: Latitude
            snap_distance_m: Distance in meters to consider nodes as "same"
            
        Returns:
            Node ID
        """
        # Check if node exists within snap distance
        result = self.db.execute(
            text("""
            SELECT id FROM pipeline_nodes
            WHERE ST_DWithin(
                geom::geography,
                ST_SetSRID(ST_Point(:lon, :lat), 4326)::geography,
                :distance
            )
            ORDER BY geom <-> ST_SetSRID(ST_Point(:lon, :lat), 4326)
            LIMIT 1
            """),
            {"lon": lon, "lat": lat, "distance": snap_distance_m}
        )
        existing = result.fetchone()
        
        if existing:
            return existing[0]
        
        # Create new node
        node = PipelineNode(
            name=f"junction_{round(lon, 5)}_{round(lat, 5)}",
            node_type='intersection',
            geom=f"SRID=4326;POINT({lon} {lat})",
            status='operating'
        )
        self.db.add(node)
        self.db.flush()
        return node.id
    
    def _map_status(self, raw_status: Any) -> str:
        """Map GEM status to our status enum."""
        if pd.isna(raw_status):
            return 'operating'
        return self.GEM_STATUS_MAP.get(str(raw_status), 'operating')
    
    def _parse_countries(self, raw: Any) -> list[str]:
        """Parse country list from GEM data."""
        if not raw or pd.isna(raw):
            return []
        # GEM uses full names like "Germany, France"
        # TODO: Map to ISO-2 codes if needed
        return [c.strip() for c in str(raw).split(",") if c.strip()]
    
    @staticmethod
    def _safe_str(val: Any) -> Optional[str]:
        """Safely convert value to string."""
        if val is None or pd.isna(val):
            return None
        return str(val).strip() or None
    
    @staticmethod
    def _safe_int(val: Any) -> Optional[int]:
        """Safely convert value to int."""
        try:
            return int(float(val)) if val and not pd.isna(val) else None
        except (ValueError, TypeError):
            return None
    
    @staticmethod
    def _safe_float(val: Any) -> Optional[float]:
        """Safely convert value to float."""
        try:
            return float(val) if val and not pd.isna(val) else None
        except (ValueError, TypeError):
            return None


def get_import_status(db: Session, job_id: int) -> Dict[str, Any]:
    """
    Get detailed status of an import job.
    
    Returns:
        Dict with job info and segment statistics
    """
    job = db.query(PipelineImportJob).filter(PipelineImportJob.id == job_id).first()
    if not job:
        raise ValueError(f"Job {job_id} not found")
    
    segment_stats = db.query(
        PipelineImportSegment.status,
        db.func.count(PipelineImportSegment.id)
    ).filter(
        PipelineImportSegment.job_id == job_id
    ).group_by(
        PipelineImportSegment.status
    ).all()
    
    return {
        "job_id": job.id,
        "filename": job.filename,
        "status": job.status,
        "started_at": job.started_at,
        "completed_at": job.completed_at,
        "total_features": job.total_features,
        "total_segments": job.total_segments,
        "processed": job.processed_segments,
        "successful": job.successful_segments,
        "failed": job.failed_segments,
        "segment_breakdown": {status: count for status, count in segment_stats},
        "error": job.error_message
    }
