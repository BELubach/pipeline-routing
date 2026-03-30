"""pipeline_segment_model

Revision ID: 01be396511b4
Revises: 215db329c700
Create Date: 2026-03-26 16:51:24.610423

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import geoalchemy2

# revision identifiers, used by Alembic.
revision: str = '01be396511b4'
down_revision: Union[str, None] = '215db329c700'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:

    op.create_table('pipeline_segments',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('IGGIELGN_id', sa.String(), nullable=True),
    sa.Column('from_node_id', sa.BigInteger(), nullable=True),
    sa.Column('to_node_id', sa.BigInteger(), nullable=True),
    sa.Column('country_code_from', sa.String(length=2), nullable=True),
    sa.Column('country_code_to', sa.String(length=2), nullable=True),
    sa.Column('is_H_gas', sa.Boolean(), nullable=False),
    sa.Column('length_km', sa.Numeric(precision=10, scale=2), nullable=False),
    sa.Column('diameter_mm', sa.Numeric(precision=10, scale=2), nullable=True),
    sa.Column('max_cap_M_m3_per_d', sa.Numeric(precision=10, scale=2), nullable=True),
    sa.Column('max_pressure_bar', sa.Numeric(precision=10, scale=2), nullable=True),
    sa.Column('geom', geoalchemy2.types.Geometry(geometry_type='LINESTRING', srid=4326, spatial_index=False, from_text='ST_GeomFromEWKT', name='geometry', nullable=False), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['from_node_id'], ['generic_nodes.id'], ),
    sa.ForeignKeyConstraint(['to_node_id'], ['generic_nodes.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_pipeline_segments_geom', 'pipeline_segments', ['geom'], unique=False, postgresql_using='gist')
    op.create_index(op.f('ix_pipeline_segments_id'), 'pipeline_segments', ['id'], unique=False)
   

def downgrade() -> None:

    op.drop_index(op.f('ix_pipeline_segments_id'), table_name='pipeline_segments')
    op.drop_index('idx_pipeline_segments_geom', table_name='pipeline_segments', postgresql_using='gist')
    op.drop_table('pipeline_segments')
