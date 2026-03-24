"""
PipelineBatchLoader — pure orchestration.
Knows about chunks, jobs, and progress; knows nothing about GEM fields.
"""

import logging

import geopandas as gpd
from pathlib import Path
from sqlalchemy.orm import Session

from app.batchdataloader.job_manager import JobManager
from app.batchdataloader.chunk_processor import ChunkProcessor
from app.dataimport.gem.segment_mapper import SegmentMapper
from app.dataimport.gem.parser import GemPipelineParser
from app.dataimport.config import EUROPE_COUNTRIES
from app.models.pipeline_import import PipelineImportJob

logger = logging.getLogger(__name__)

class PipelineBatchLoader:
    """
    Drives chunked import of a GeoDataFrame through a SegmentMapper,
    tracking progress and supporting resume via Job/Chunk DB records.
    """

    EUROPE_BBOX = (-30, 20, 60, 75)

    def __init__(self, db: Session):
        self.db = db
        self._jobs = JobManager(db)
        self._chunks = ChunkProcessor(db)
        self._parser = GemPipelineParser()
        self._mapper = SegmentMapper(db, self._parser)

    def load_file(
        self,
        geojson_path: str,
        batch_size: int = 100,
        europe_only: bool = True,
        existing_job: PipelineImportJob | None = None,
    ) -> PipelineImportJob:
        filepath = Path(geojson_path)
        if not filepath.exists():
            raise FileNotFoundError(f"GeoJSON file not found: {geojson_path}")

        job = self._jobs.create_or_resume(filepath.name, existing_job)

        try:
            gdf = self._load_geodataframe(geojson_path, europe_only)
            self._jobs.update_totals(job, len(gdf), len(gdf))
            self._run_job(job, gdf, batch_size)
        except Exception as exc:
            logger.error(f"Import job {job.id} failed: {exc}")
            self._jobs.fail(job, exc)
            raise

        return job

    # ── private ───────────────────────────────────────────────────────────────

    def _load_geodataframe(self, path: str, europe_only: bool) -> gpd.GeoDataFrame:
        logger.info("Reading GeoJSON file…")
        gdf = gpd.read_file(path).to_crs(epsg=4326)
        gdf = gdf.explode(index_parts=False).reset_index(drop=True)
        gdf = gdf[gdf.geometry.geom_type == "LineString"].copy()

        if europe_only:
            # Bbox pre-filter for performance, then precise country filter
            lon0, lat0, lon1, lat1 = self.EUROPE_BBOX
            gdf = gdf.cx[lon0:lon1, lat0:lat1]
            gdf = self._filter_by_country(gdf)
            logger.info(f"Filtered to Europe scope: {len(gdf)} segments")

        return gdf

    def _filter_by_country(self, gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
        """
        Keep rows where at least one parsed country code is in EUROPE_COUNTRIES.
        Rows with no country data are kept (avoids silently dropping valid data).
        """
        def row_in_scope(row) -> bool:
            return self._parser.is_in_scope(self._parser.parse_row(row))

        mask = [row_in_scope(row) for _, row in gdf.iterrows()]
        return gdf[mask].copy()

    def _run_job(self, job, gdf, batch_size):
        total = len(gdf)
        num_chunks = (total + batch_size - 1) // batch_size
        completed = self._jobs.completed_chunk_indices(job.id)

        processed = success_count = failed_count = 0

        for chunk_idx in range(num_chunks):
            start = chunk_idx * batch_size
            end = min(start + batch_size, total)

            if chunk_idx in completed:
                processed += end - start
                continue

            chunk_success, chunk_failed = self._process_chunk(job, chunk_idx, start, end, gdf)
            processed += end - start
            success_count += chunk_success
            failed_count += chunk_failed

            self._jobs.update_progress(job, processed, success_count, failed_count)
            logger.info(
                f"Chunk {chunk_idx + 1}/{num_chunks}: "
                f"{chunk_success} ok, {chunk_failed} failed — {processed}/{total}"
            )

        self._jobs.finalize(job, success_count, failed_count)

    def _process_chunk(self, job, chunk_idx, start, end, gdf):
        chunk = self._chunks.get_or_create(job.id, chunk_idx, start, end)
        self._chunks.mark_running(chunk)

        chunk_success = chunk_failed = 0
        for idx in range(start, end):
            if self._chunks.segment_already_processed(job.id, idx):
                continue
            success, failed = self._process_segment(job.id, idx, gdf.iloc[idx])
            chunk_success += success
            chunk_failed += failed

        self._chunks.mark_done(chunk, chunk_failed)
        return chunk_success, chunk_failed

    def _process_segment(self, job_id, idx, row):
        try:
            edge_id, source_id, target_id = self._mapper.map_row(row, row.geometry)
            self._chunks.record_segment_success(job_id, idx, row, edge_id, source_id, target_id)
            return 1, 0
        except Exception as exc:
            logger.error(f"Segment {idx} failed: {exc}")
            self.db.rollback()
            self._chunks.record_segment_failure(job_id, idx, row, exc)
            return 0, 1
