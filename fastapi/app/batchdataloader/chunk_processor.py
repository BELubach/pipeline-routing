

import pandas as pd
from datetime import datetime
from sqlalchemy.orm import Session
from app.dataimport.value_parser import ValueParser
from app.models.pipeline_import import PipelineImportChunk, PipelineImportSegment

class ChunkProcessor:
    """
    Manages PipelineImportChunk and PipelineImportSegment records
    for a single batch window.
    """

    def __init__(self, db: Session):
        self.db = db

    def get_or_create(
        self, job_id: int, chunk_idx: int, start: int, end: int
    ) -> PipelineImportChunk:
        chunk = (
            self.db.query(PipelineImportChunk)
            .filter_by(job_id=job_id, chunk_index=chunk_idx)
            .first()
        )
        if not chunk:
            chunk = PipelineImportChunk(
                job_id=job_id,
                chunk_index=chunk_idx,
                start_segment_index=start,
                end_segment_index=end - 1,
                status="pending",
            )
            self.db.add(chunk)
            self.db.commit()
            self.db.refresh(chunk)
        return chunk

    def mark_running(self, chunk: PipelineImportChunk) -> None:
        chunk.status = "running"
        self.db.commit()

    def mark_done(self, chunk: PipelineImportChunk, failed_count: int) -> None:
        chunk.status = "success" if failed_count == 0 else "failed"
        if failed_count:
            chunk.error_message = f"{failed_count} segment(s) failed in chunk {chunk.chunk_index}"
        chunk.processed_at = datetime.utcnow()
        self.db.commit()

    def segment_already_processed(self, job_id: int, segment_idx: int) -> bool:
        return bool(
            self.db.query(PipelineImportSegment).filter(
                PipelineImportSegment.job_id == job_id,
                PipelineImportSegment.segment_index == segment_idx,
                PipelineImportSegment.status.in_(["success", "failed", "skipped"]),
            ).first()
        )

    def record_segment_success(
        self,
        job_id: int,
        idx: int,
        row: pd.Series,
        edge_id: int,
        source_id: int,
        target_id: int,
    ) -> None:
        seg = self._make_segment(job_id, idx, row, status="success")
        seg.edge_id = edge_id
        seg.source_node_id = source_id
        seg.target_node_id = target_id
        self.db.add(seg)

    def record_segment_failure(
        self, job_id: int, idx: int, row: pd.Series, error: Exception
    ) -> None:
        seg = self._make_segment(job_id, idx, row, status="failed")
        seg.error_message = str(error)[:1000]
        self.db.add(seg)

    def _make_segment(
        self, job_id: int, idx: int, row: pd.Series, status: str
    ) -> PipelineImportSegment:
        c = ValueParser
        return PipelineImportSegment(
            job_id=job_id,
            gem_id=c.safe_str(row.get("GEM Unit ID")),
            pipeline_name=c.safe_str(row.get("Pipeline Name")),
            segment_index=int(idx),
            status=status,
        )

