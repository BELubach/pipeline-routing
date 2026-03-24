# Pipeline Infrastructure Integration

This document describes the gas pipeline infrastructure integration for the FastAPI application.

## Overview

## Database Schema

### Tables

#### `pipeline_nodes`
Pipeline network vertices (compressor stations, hubs, LNG terminals, etc.)

Key fields:
- `id` - Primary key
- `name` - Node name
- `node_type` - Type: compressor_station, border_crossing, hub, lng_terminal, storage, production, intersection
- `country` - ISO 3166-1 alpha-2 country code
- `geom` - PostGIS Point geometry (SRID 4326)
- `is_trading_hub` - Boolean flag for trading hubs
- `hub_code` - Trading hub code (e.g., 'TTF', 'NCG')
- `lng_capacity_bcm` - LNG terminal capacity in bcm/year
- `status` - operating, construction, planned, decommissioned

#### `pipeline_edges`
Pipeline segments connecting nodes (for pgRouting)

Key fields:
- `id` - Primary key
- `source` - Foreign key to pipeline_nodes
- `target` - Foreign key to pipeline_nodes
- `geom` - PostGIS LineString geometry (SRID 4326)
- `pipeline_name` - Pipeline name (e.g., 'Nord Stream', 'OPAL')
- `operator` - Pipeline operator
- `diameter_mm` - Pipe diameter in millimeters
- `capacity_mcm_d` - Capacity in million cubic meters per day
- `length_km` - Segment length in kilometers
- `cost_distance_km` - Geographic distance cost
- `cost_tariff_eur_mwh` - Transmission tariff cost (€/MWh)
- `cost_composite` - Combined cost metric (primary routing cost)
- `reverse_cost_*` - Costs for reverse direction
- `status` - operating, construction, planned, decommissioned, suspended

#### `tariff_rules`
Lookup table for transmission tariff estimation

Used to compute costs when real tariff data is unavailable.

## API Endpoints

All endpoints are available at `/api/v1/pipelines/`

### GET `/api/v1/pipelines/route`

Find the cheapest gas pipeline route between two coordinates.

**Query Parameters:**
- `start_lon` (required) - Source longitude (WGS84)
- `start_lat` (required) - Source latitude (WGS84)
- `end_lon` (required) - Destination longitude (WGS84)
- `end_lat` (required) - Destination latitude (WGS84)
- `cost_type` - Cost metric: `composite` (default), `tariff`, `distance`
- `max_snap_km` - Max distance to snap to nearest node (default: 200.0)

**Example:**
```bash
curl "http://localhost:8000/api/v1/pipelines/route?start_lon=4.9&start_lat=52.3&end_lon=13.4&end_lat=52.5&cost_type=composite"
```

**Response:**
```json
{
  "source_lon": 4.9,
  "source_lat": 52.3,
  "dest_lon": 13.4,
  "dest_lat": 52.5,
  "start_node_id": 123,
  "end_node_id": 456,
  "total_cost_eur_mwh": 1.23,
  "total_km": 450.5,
  "cost_type": "composite",
  "segments": [
    {
      "seq": 1,
      "node_id": 123,
      "node_name": "TTF Hub",
      "edge_id": 789,
      "pipeline_name": "OPAL",
      "segment_cost_eur_mwh": 0.45,
      "cumulative_cost_eur_mwh": 0.45,
      "segment_km": 250.3,
      "geometry": {...}
    }
  ],
  "route_geojson": {
    "type": "FeatureCollection",
    "features": [...]
  }
}
```

### GET `/api/v1/pipelines/nearest-nodes`

Find the nearest pipeline nodes to a coordinate.

**Query Parameters:**
- `lon` (required) - Longitude
- `lat` (required) - Latitude
- `max_km` - Max search distance in km (default: 200.0)
- `node_type` - Filter by node type (optional)

**Example:**
```bash
curl "http://localhost:8000/api/v1/pipelines/nearest-nodes?lon=4.9&lat=52.3&max_km=100"
```

### GET `/api/v1/pipelines/nodes`

List all pipeline nodes with optional filters.

**Query Parameters:**
- `node_type` - Filter by node type (optional)
- `country` - Filter by ISO country code (optional)
- `hubs_only` - Only return trading hubs (default: false)

**Example:**
```bash
# Get all trading hubs
curl "http://localhost:8000/api/v1/pipelines/nodes?hubs_only=true"

# Get all LNG terminals
curl "http://localhost:8000/api/v1/pipelines/nodes?node_type=lng_terminal"

# Get all nodes in Germany
curl "http://localhost:8000/api/v1/pipelines/nodes?country=DE"
```

### GET `/api/v1/pipelines/nodes/{node_id}/reachable`

Get all nodes reachable from a given node within a cost budget.

**Query Parameters:**
- `max_cost` - Max cost in €/MWh (default: 10.0)

**Example:**
```bash
curl "http://localhost:8000/api/v1/pipelines/nodes/123/reachable?max_cost=5.0"
```

## Management Commands

The `manage.py` script provides several utilities:

```bash
# Import pipeline data
python manage.py import-pipelines [--geojson PATH] [--global-scope]

# Create admin user
python manage.py create-admin --email admin@example.com --password secret --name "Admin User"

# Initialize database
python manage.py init-db

# Open database shell (psql)
python manage.py db-shell

# Execute SQL file
python manage.py run-sql path/to/file.sql
```

## Cost Optimization

The routing algorithm supports three cost metrics:

1. **composite** (default) - Best estimate combining tariff and distance
   - Uses real tariff data when available
   - Falls back to distance-based estimation
   - Most realistic for real-world scenarios

2. **tariff** - Actual transmission tariffs (€/MWh)
   - Uses known tariff data from ENTSOG and regulators
   - Estimated where data unavailable
   - Best for cost analysis

3. **distance** - Pure geographic distance (km)
   - Shortest path by distance only
   - Ignores tariffs and capacity
   - Useful for technical analysis

## Data Sources

Pipeline data from:
- **Global Energy Monitor** - [Global Gas Infrastructure Tracker](https://globalenergymonitor.org/projects/global-gas-infrastructure-tracker/)
- **ENTSOG** - European Network of Transmission System Operators for Gas
- **Tools4MSP** - [Europe Gas Pipelines](https://geoplatform.tools4msp.eu/layers/geonode:Gas_pipelines)

Tariff data from:
- National regulatory authorities (BNetzA, ACM, CRE, CREG, Ofgem)
- ENTSOG CAM Network Code

## Files Added/Modified

### New Files
- `app/models/pipeline.py` - SQLAlchemy models for pipeline infrastructure
- `app/api/v1/endpoints/pipelines.py` - FastAPI routing endpoints
- `manage.py` - Management CLI script
- `boot/pipeline_functions.sql` - Database functions and views to run after migration
- `boot/import_gem_pipelines.py` - GEM pipeline data import script
- `boot/smoke_queries.sql` - Test queries to verify setup
- `PIPELINE_README.md` - This documentation

### Modified Files
- `app/models/__init__.py` - Added pipeline model imports
- `app/db/base.py` - Added pipeline models to metadata
- `app/api/v1/api.py` - Added pipelines router
- `docker-compose.yml` - Updated to pgrouting image
- `requirements.txt` - Added pipeline dependencies
- `alembic/versions/*_add_pipeline_infrastructure_models.py` - Migration for pipeline tables

## Troubleshooting

### Migration Issues

If migration fails with missing extensions:
```bash
# Connect to database and enable extensions manually
psql -h localhost -p 5433 -U postgres -d fastapi_db
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS pgrouting;
\q

# Then retry migration
alembic upgrade head
```

### Import Errors

If import fails with "No module named 'psycopg2'":
```bash
pip install psycopg2-binary
```

If import fails with "No module named 'geopandas'":
```bash
pip install geopandas pandas shapely
```

### Database Connection

Check your `.env` file has correct database settings:
```
POSTGRES_HOST=localhost
POSTGRES_PORT=5433
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=fastapi_db
```

## Verify Installation

After setup, verify everything works by running the smoke tests:

```bash
python manage.py run-sql boot/smoke_queries.sql
```

These queries test:
- ✅ Extensions loaded (PostGIS, pgRouting)
- ✅ Node and edge counts
- ✅ Cost calculation coverage
- ✅ Nearest node search
- ✅ Route finding between nodes
- ✅ Coordinate-based routing
- ✅ Reachability analysis
- ✅ Graph connectivity
- ✅ Most expensive segments

## Next Steps

1. **Test the API**: Use the `/docs` endpoint to explore the interactive API documentation
2. **Import more data**: Download and import full GeoJSON datasets
3. **Customize tariffs**: Update `tariff_rules` table with more accurate regional data
4. **Add monitoring**: Track routing performance and popular routes
5. **Extend functionality**: Add capacity constraints, flow simulation, etc.

## License

Pipeline data from Global Energy Monitor is licensed under CC BY 4.0.
