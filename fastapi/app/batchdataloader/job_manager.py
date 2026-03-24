

from app.models.pipeline_import import PipelineImportJob, PipelineImportChunk
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional

class JobManager:
    """
    Creates, resumes, and finalises PipelineImportJob records.
    Single responsibility: job-level DB state only.
    """

    def __init__(self, db: Session):
        self.db = db

    def create_or_resume(
        self, filename: str, existing: Optional[PipelineImportJob] = None
    ) -> PipelineImportJob:
        if existing is not None:
            return existing
        job = PipelineImportJob(filename=filename, status="running")
        self.db.add(job)
        self.db.commit()
        self.db.refresh(job)
        return job

    def update_totals(self, job: PipelineImportJob, total_features: int, total_segments: int) -> None:
        job.total_features = total_features
        job.total_segments = total_segments
        self.db.commit()

    def update_progress(self, job: PipelineImportJob, processed: int, success: int, failed: int) -> None:
        job.processed_segments = processed
        job.successful_segments = success
        job.failed_segments = failed
        self.db.commit()

    def finalize(self, job: PipelineImportJob, success: int, failed: int) -> None:
        job.successful_segments = success
        job.failed_segments = failed
        job.completed_at = datetime.utcnow()
        job.status = "completed" if failed == 0 else "partial"
        self.db.commit()

    def fail(self, job: PipelineImportJob, error: Exception) -> None:
        job.status = "failed"
        job.error_message = str(error)[:1000]
        job.completed_at = datetime.utcnow()
        self.db.commit()

    def completed_chunk_indices(self, job_id: int) -> set[int]:
        return {
            c.chunk_index
            for c in self.db.query(PipelineImportChunk).filter(
                PipelineImportChunk.job_id == job_id,
                PipelineImportChunk.status == "success",
            )
        }
