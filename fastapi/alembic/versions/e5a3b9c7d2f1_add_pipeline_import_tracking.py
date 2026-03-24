"""add pipeline import tracking tables

Revision ID: e5a3b9c7d2f1
Revises: 0490a000984a
Create Date: 2026-03-23 13:20:00

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e5a3b9c7d2f1'
down_revision = '0490a000984a'
branch_label = None
depends_on = None


def upgrade():
    # Create pipeline_import_jobs table
    op.create_table(
        'pipeline_import_jobs',
        sa.Column('id', sa.BigInteger(), nullable=False, autoincrement=True),
        sa.Column('filename', sa.Text(), nullable=False),
        sa.Column('started_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('status', sa.Text(), nullable=False, server_default='running'),
        sa.Column('total_features', sa.Integer(), nullable=True),
        sa.Column('total_segments', sa.Integer(), nullable=True),
        sa.Column('processed_segments', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('successful_segments', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('failed_segments', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint(
            "status IN ('running', 'completed', 'failed', 'partial')",
            name='check_job_status'
        )
    )
    op.create_index('idx_import_job_status', 'pipeline_import_jobs', ['status'])
    

    # Create pipeline_import_segments table
    op.create_table(
        'pipeline_import_segments',
        sa.Column('id', sa.BigInteger(), nullable=False, autoincrement=True),
        sa.Column('job_id', sa.BigInteger(), nullable=False),
        sa.Column('gem_id', sa.Text(), nullable=True),
        sa.Column('pipeline_name', sa.Text(), nullable=True),
        sa.Column('segment_index', sa.Integer(), nullable=True),
        sa.Column('source_node_id', sa.BigInteger(), nullable=True),
        sa.Column('target_node_id', sa.BigInteger(), nullable=True),
        sa.Column('edge_id', sa.BigInteger(), nullable=True),
        sa.Column('status', sa.Text(), nullable=False, server_default='pending'),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('processed_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint(
            "status IN ('success', 'failed', 'skipped')",
            name='check_segment_status'
        )
    )
    op.create_index('idx_import_seg_job_status', 'pipeline_import_segments', ['job_id', 'status'])
    op.create_index('idx_import_seg_gem_id', 'pipeline_import_segments', ['gem_id'])


def downgrade():
    op.drop_index('idx_import_seg_gem_id', table_name='pipeline_import_segments')
    op.drop_index('idx_import_seg_job_status', table_name='pipeline_import_segments')
    op.drop_table('pipeline_import_segments')

    op.drop_index('idx_import_job_status', table_name='pipeline_import_jobs')
    op.drop_table('pipeline_import_jobs')
