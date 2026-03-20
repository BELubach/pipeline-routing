# Boot Scripts - Pipeline Infrastructure Setup

This folder contains initialization scripts to set up the gas pipeline infrastructure.

## Required Setup Steps (Run Once)

After running `alembic upgrade head`, execute these in order:

### 1. Create Database Functions & Views 

```bash
python manage.py run-sql boot/pipeline_functions.sql
```

**What it does:**
- Creates PostgreSQL functions for routing (`nearest_node`, `find_cheapest_gas_route`, etc.)
- Creates the `pipeline_routing_graph` view for pgRouting
- Seeds tariff rules with ENTSOG reference data
- Enables PostGIS and pgRouting extensions

**Required:** Yes, before importing data

---

### 2. Import Pipeline Data 

**Option A - Quick Start (Recommended):**
```bash
python manage.py import-pipelines --seed-nodes-only
```

Seeds ~50 well-known hubs, LNG terminals, and border crossings.

**Option B - Full Import:**
1. Download GeoJSON from [Global Gas Infrastructure Tracker](https://globalenergymonitor.org/projects/global-gas-infrastructure-tracker/)
2. Save to `./data/europe_gas_pipelines.geojson`
3. Run:
   ```bash
   python manage.py import-pipelines --geojson ./data/europe_gas_pipelines.geojson
   ```

**Required:** Yes, to have data to route through

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

---

## Files in this Folder

| File | Purpose | Run When |
|------|---------|----------|
| `pipeline_functions.sql` | Creates DB functions, views, and seed data | After Alembic migration |
| `import_gem_pipelines.py` | Imports GEM pipeline GeoJSON data | After functions are created |
| `smoke_queries.sql` | Test queries to verify setup | After data import (optional) |

---

## Common Issues

**"Extension postgis does not exist"**
- Make sure you're using the pgrouting Docker image
- Check `docker-compose.yml` uses: `pgrouting/pgrouting:16-3.6-3.6.2`

**"Function nearest_node does not exist"**
- Run `python manage.py run-sql boot/pipeline_functions.sql`

**"No pipeline nodes found"**
- Run `python manage.py import-pipelines --seed-nodes-only`

**"ModuleNotFoundError: No module named 'psycopg2'"**
- Install dependencies: `pip install -r requirements.txt`

---

## Re-running Scripts

These scripts are **idempotent** where possible:

- `pipeline_functions.sql` - Uses `CREATE OR REPLACE`, safe to re-run
- `import_gem_pipelines.py` - Uses `ON CONFLICT DO NOTHING`, safe to re-run
- `smoke_queries.sql` - Read-only queries, always safe

---

## sMore Information

See [PIPELINE_README.md](../PIPELINE_README.md) in the project root for:
- Complete API documentation
- Detailed architecture overview
- Data source information
- Troubleshooting guide
