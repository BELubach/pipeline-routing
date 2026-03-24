# Boot Scripts - Pipeline Infrastructure Setup
This folder contains initialization scripts to set up the gas pipeline infrastructure.


---

## Files in this Folder

| File | Purpose | Run When |
|------|---------|----------|
| `/db_setup/pipeline_functions.sql` | Creates DB functions, views, and seed data | After Alembic migration |
| `/db_setup/import_gem_pipelines.py` | Imports GEM pipeline GeoJSON data | After functions are created |
| `/db_checks/check_pipeline_data.py` | Node/edge counts, cost status, nearest node checks | After data import |
| `/db_checks/check_edge_connectivity.py` | Self-loop, edge validity, connectivity checks | After data import |
| `/db_checks/detailed_routing_debug.py` | Step-by-step routing diagnosis, network checks | After data import (optional) |
| `/db_checks/find_working_route.py` | Finds connected nodes for routing tests | After data import (optional) |
| `/db_checks/debug_routing.sql` | Raw SQL diagnostic queries | After data import (optional) |
| `/db_checks/smoke_queries.sql` | Test queries to verify setup | After data import (recommended) |

---


### 1. Create Database Functions & Views 

```bash
python manage.py run-sql boot/pipeline_functions.sql
```

**What it does:**
- Creates PostgreSQL functions for routing (`nearest_node`, `find_cheapest_gas_route`, etc.)
- Creates the `pipeline_routing_graph` view for pgRouting
- Seeds tariff rules with ENTSOG reference data
- Enables PostGIS and pgRouting extensions


---

### 2. Import Pipeline Data 

**Option A - Quick Start (Recommended):**
```bash
python manage.py import-pipelines
```

Seeds ~50 well-known hubs, LNG terminals, and border crossings.

**Option B - Full Import:**
1. Download GeoJSON from [Global Gas Infrastructure Tracker](https://globalenergymonitor.org/projects/global-gas-infrastructure-tracker/)
2. Save to `./data/GEM-GGIT-Gas-Pipelines-2025-11.geojson`
3. Run:
   ```bash
  python manage.py import-pipelines --geojson ./data/GEM-GGIT-Gas-Pipelines-2025-11.geojson --global-scope
   ```
---

### 3. Verify Setup 

```bash
python manage.py run-sql boot/smoke_queries.sql
```

**What it does:**
- Tests that extensions are loaded
- Checks node/edge counts
- Verifies cost calculations
- Tests routing functions
- Checks graph connectivity

**Required:** No, but recommended to confirm everything works



## Common Issues

**"Extension postgis does not exist"**
- Make sure you're using the pgrouting Docker image
- Check `docker-compose.yml` uses: `pgrouting/pgrouting:16-3.5-4.0`

**"Function nearest_node does not exist"**
- Run `python manage.py run-sql boot/pipeline_functions.sql`

**"No pipeline nodes found"**
- Run `python manage.py import-pipelines`

**"ModuleNotFoundError: No module named 'psycopg2'"**
- Install dependencies: `pip install -r requirements.txt`

---

## Re-running Scripts

These scripts are **idempotent** where possible:

- `pipeline_functions.sql` - Uses `CREATE OR REPLACE`, safe to re-run
- `import_gem_pipelines.py` - Uses `ON CONFLICT DO NOTHING`, safe to re-run
- `smoke_queries.sql` - Read-only queries, always safe

---

