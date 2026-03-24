"""
Translates a parsed dict (from GemPipelineParser) into DB objects.
Owns node snapping and edge construction — no field-name knowledge here.
"""

from shapely.geometry import LineString
from geoalchemy2.shape import from_shape
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.models.pipeline import PipelineEdge, PipelineNode
from app.dataimport.gem.parser import GemPipelineParser


class SegmentMapper:
    """
    Given a parsed row dict and a LineString geometry, produces
    PipelineNode + PipelineEdge DB objects via flush (no commit).
    """

    SNAP_DISTANCE_M = 500

    def __init__(self, db: Session, parser: GemPipelineParser):
        self.db = db
        self._parser = parser

    def map_row(self, row, geom: LineString) -> tuple[int, int, int]:
        """
        Full pipeline: parse row → snap/create nodes → create edge.
        Returns (edge_id, source_node_id, target_node_id).
        """
        parsed = self._parser.parse_row(row)
        return self.map_parsed(parsed, geom)

    def map_parsed(self, parsed: dict, geom: LineString) -> tuple[int, int, int]:
        """
        Create nodes and edge from an already-parsed dict.
        Separated so callers can parse and filter before hitting the DB.
        """
        coords = list(geom.coords)
        if len(coords) < 2:
            raise ValueError("LineString must have at least 2 points")

        source_id = self._get_or_create_node(*coords[0])
        target_id = self._get_or_create_node(*coords[-1])
        edge = self._build_edge(geom, parsed, source_id, target_id)

        self.db.add(edge)
        self.db.flush()
        return edge.id, source_id, target_id

    # ── private ───────────────────────────────────────────────────────────────

    def _build_edge(
        self,
        geom: LineString,
        parsed: dict,
        source_id: int,
        target_id: int,
    ) -> PipelineEdge:
        return PipelineEdge(
            source=source_id,
            target=target_id,
            geom=from_shape(geom, srid=4326),
            pipeline_name=parsed["pipeline_name"],
            source_name=parsed["source_name"],
            operator=parsed["operator"],
            status=parsed["status"],
            diameter_mm=parsed["diameter_mm"],
            capacity_mcm_d=parsed["capacity_mcm_d"],
            length_km=parsed["length_km"],
            year_built=parsed["year_built"],
            country_codes=parsed["country_codes"],
            gem_id=parsed["gem_id"],
            tariff_type="estimated",
        )

    def _get_or_create_node(self, lon: float, lat: float) -> int:
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
            {"lon": lon, "lat": lat, "distance": self.SNAP_DISTANCE_M},
        )
        existing = result.fetchone()
        if existing:
            return existing[0]

        node = PipelineNode(
            name=f"junction_{round(lon, 5)}_{round(lat, 5)}",
            node_type="intersection",
            geom=f"SRID=4326;POINT({lon} {lat})",
            status="operating",
        )
        self.db.add(node)
        self.db.flush()
        return node.id