"""0001_initial_postgis_setup

Initial setup of PostGIS and pgRouting extensions
"""

from alembic import op
import os

# Alembic revision identifiers
revision = '0001_initial_postgis_setup'
down_revision = None
branch_labels = None
depends_on = None



from alembic import op

def upgrade():
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis;")
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis_topology;")
    op.execute("CREATE EXTENSION IF NOT EXISTS pgrouting;")
    # optional: PostGIS version check
    # result = op.get_bind().execute("SELECT PostGIS_Version();")
    # print(result.fetchone())

def downgrade():
    """Optional: drop extensions (use with caution)"""
    # Dropping extensions may break dependent objects; typically skipped in production
    op.execute("DROP EXTENSION IF EXISTS pgrouting CASCADE;")
    op.execute("DROP EXTENSION IF EXISTS postgis_topology CASCADE;")
    op.execute("DROP EXTENSION IF EXISTS postgis CASCADE;")