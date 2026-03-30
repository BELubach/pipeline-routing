"""pipeline border nodes 

Revision ID: c70b89f2f410
Revises: f4c03b140a09
Create Date: 2026-03-25 20:33:13.726984

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import geoalchemy2

revision: str = 'c70b89f2f410'
down_revision: Union[str, None] = 'f4c03b140a09'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('border_nodes',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('IGGIELGN_id', sa.String(), nullable=True),
    sa.Column('name', sa.String(), nullable=True),
    sa.Column('geom', geoalchemy2.types.Geometry(geometry_type='POINT', srid=4326, spatial_index=False, from_text='ST_GeomFromEWKT', name='geometry', nullable=False), nullable=False),
    sa.Column('country_code', sa.String(), nullable=False),
    sa.Column('from_country', sa.String(), nullable=False),
    sa.Column('to_country', sa.String(), nullable=False),
    sa.Column('from_TSO', sa.String(), nullable=True),
    sa.Column('to_TSO', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_border_nodes_geom', 'border_nodes', ['geom'], unique=False, postgresql_using='gist')
 
def downgrade() -> None:
  
    op.drop_index('idx_border_nodes_geom', table_name='border_nodes', postgresql_using='gist')
    op.drop_table('border_nodes')
