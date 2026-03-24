# Chunk tracking model for performant batch import
from sqlalchemy import ForeignKey, CheckConstraint, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.session import Base
from sqlalchemy import (
    Column, BigInteger, Integer, Text, DateTime, Index
)

class PipelineImportChunk(Base):
    __tablename__ = 'pipeline_import_chunks'
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    job_id = Column(BigInteger, ForeignKey('pipeline_import_jobs.id'), nullable=False)
    chunk_index = Column(Integer, nullable=False)
    start_segment_index = Column(Integer, nullable=False)
    end_segment_index = Column(Integer, nullable=False)
    status = Column(Text, nullable=False, server_default='pending')
    processed_at = Column(DateTime(timezone=True), server_default=func.now())
    error_message = Column(Text, nullable=True)

    __table_args__ = (
        UniqueConstraint('job_id', 'chunk_index', name='uq_job_chunk'),
        CheckConstraint("status IN ('pending', 'running', 'success', 'failed')", name='check_chunk_status'),
    )

    job = relationship('PipelineImportJob', backref='chunks')


class PipelineImportJob(Base):
    """
    Tracks batch import jobs for pipeline data.
    One job = one full GeoJSON file import attempt.
    """
    __tablename__ = "pipeline_import_jobs"
    
    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    
    filename = Column(Text, nullable=False)  
    started_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    completed_at = Column(DateTime(timezone=True))
    
    status = Column(
        Text,
        nullable=False,
        default='running',
        server_default='running'
    )  # 'running', 'completed', 'failed', 'partial'
    
    total_features = Column(Integer)  
    total_segments = Column(Integer) 
    processed_segments = Column(Integer, default=0)
    successful_segments = Column(Integer, default=0)
    failed_segments = Column(Integer, default=0)
    
    
    error_message = Column(Text)  
    
    def __repr__(self):
        return f"<PipelineImportJob(id={self.id}, file={self.filename}, status={self.status})>"


class PipelineImportSegment(Base):
    """
    Tracks individual segment import within a job.
    Each row = one pipeline segment (line geometry) processed.
    """
    __tablename__ = "pipeline_import_segments"
    
    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    
    job_id = Column(BigInteger, nullable=False, index=True)
    
    gem_id = Column(Text, index=True)  
    pipeline_name = Column(Text)
    segment_index = Column(Integer)  
    
    source_node_id = Column(BigInteger)  
    target_node_id = Column(BigInteger)
    edge_id = Column(BigInteger) 

    status = Column(
        Text,
        nullable=False,
        default='pending'
    )  # 'pending', 'success', 'failed', 'skipped'
    
    error_message = Column(Text)
    processed_at = Column(DateTime(timezone=True), server_default=func.now())
    
    def __repr__(self):
        return f"<PipelineImportSegment(job={self.job_id}, gem_id={self.gem_id}, seg={self.segment_index}, status={self.status})>"


Index('idx_import_seg_job_status', PipelineImportSegment.job_id, PipelineImportSegment.status)
Index('idx_import_seg_gem_id', PipelineImportSegment.gem_id)
Index('idx_import_job_status', PipelineImportJob.status)
