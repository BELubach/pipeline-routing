"""lng_terminal model

Revision ID: 92965d81aefc
Revises: 01be396511b4
Create Date: 2026-03-31 10:31:20.157121

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import geoalchemy2

# revision identifiers, used by Alembic.
revision: str = '92965d81aefc'
down_revision: Union[str, None] = '01be396511b4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('lng_terminals',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('IGGIELGN_id', sa.String(), nullable=False),
    sa.Column('name', sa.String(), nullable=True),
    sa.Column('geom', geoalchemy2.types.Geometry(geometry_type='POINT', spatial_index=False, srid=4326, from_text='ST_GeomFromEWKT', name='geometry', nullable=False), nullable=False),
    sa.Column('country_code', sa.String(), nullable=False),
    sa.Column('max_cap_store2pipe_M_m3_per_d', sa.Numeric(precision=10, scale=2), nullable=True),
    sa.Column('start_year', sa.Integer(), nullable=True),
    sa.Column('from_TSO', sa.String(), nullable=True),
    sa.Column('to_TSO', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_lng_terminals_geom', 'lng_terminals', ['geom'], unique=False, postgresql_using='gist')
    op.create_index(op.f('ix_lng_terminals_id'), 'lng_terminals', ['id'], unique=False)
   


def downgrade() -> None:
    op.drop_index(op.f('ix_lng_terminals_id'), table_name='lng_terminals')
    op.drop_index('idx_lng_terminals_geom', table_name='lng_terminals', postgresql_using='gist')
    op.drop_table('lng_terminals')
