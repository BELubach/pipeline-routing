"""add maritime_routes table

Revision ID: 936d25046abd
Revises: 0dca8017094f
Create Date: 2026-06-18 14:52:15.919273

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import geoalchemy2

# revision identifiers, used by Alembic.
revision: str = '936d25046abd'
down_revision: Union[str, None] = '0dca8017094f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.create_table(
        "maritime_routes",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("geometry", geoalchemy2.types.Geometry(geometry_type="LINESTRING", srid=4326, spatial_index=False),  nullable=True),
        sa.Column("pass", sa.Text, nullable=True),
    )

    op.create_index('ix_maritime_routes_geom', 'maritime_routes', ['geometry'], unique=False, postgresql_using='gist')
    op.create_index(op.f('ix_maritime_routes_id'), 'maritime_routes', ['id'], unique=False)

def downgrade():
    op.drop_table("maritime_routes")