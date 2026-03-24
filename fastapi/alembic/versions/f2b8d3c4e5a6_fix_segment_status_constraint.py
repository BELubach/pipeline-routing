"""fix segment status constraint to include pending

Revision ID: f2b8d3c4e5a6
Revises: e5a3b9c7d2f1
Create Date: 2026-03-24 11:15:00

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f2b8d3c4e5a6'
down_revision = 'e5a3b9c7d2f1'
branch_label = None
depends_on = None


def upgrade():
    # Drop old constraint
    op.drop_constraint('check_segment_status', 'pipeline_import_segments', type_='check')
    
    # Add new constraint that includes 'pending'
    op.create_check_constraint(
        'check_segment_status',
        'pipeline_import_segments',
        "status IN ('pending', 'success', 'failed', 'skipped')"
    )


def downgrade():
    # Drop new constraint
    op.drop_constraint('check_segment_status', 'pipeline_import_segments', type_='check')
    
    # Restore old constraint
    op.create_check_constraint(
        'check_segment_status',
        'pipeline_import_segments',
        "status IN ('success', 'failed', 'skipped')"
    )
