# Multimodal Routing System Setup Guide

## Quick Start

Follow these steps to set up and start using the multimodal routing system.

### 1. Run the SQL Migration

Execute the routing functions SQL file to create all necessary database objects:

```bash
# From the fastapi directory
cd fastapi

# Using psql (adjust connection details)
psql -h localhost -U your_user -d your_database -f alembic/sql/multimodal_routing_functions.sql

# OR using Python with SQLAlchemy
python -c "
from app.db.session import engine
with open('alembic/sql/multimodal_routing_functions.sql') as f:
    sql = f.read()
    with engine.connect() as conn:
        conn.execute(sql)
        conn.commit()
"
```

### 2. Verify Setup

Check that all components were created successfully:

```sql
-- Check materialized views
SELECT COUNT(*) FROM unified_nodes;
SELECT COUNT(*) FROM unified_edges;
SELECT COUNT(*) FROM shipping_lane_endpoints;

-- Check that functions exist
SELECT routine_name 
FROM information_schema.routines 
WHERE routine_schema = 'public' 
  AND routine_type = 'FUNCTION'
  AND routine_name LIKE '%route%';
```

### 3. Initialize Terminal Connections

Create the network connections for LNG terminals:

```sql
-- This creates virtual edges connecting terminals to pipelines and shipping
SELECT * FROM create_terminal_connections(50.0, 100.0);

-- Verify connections were created
SELECT COUNT(*) FROM temp_terminal_edges;
```

### 4. Test the Routing System

Try a simple route calculation:

```sql
-- Find nearest node to a coordinate
SELECT * FROM nearest_node(5.0, 52.0, 200.0);

-- Calculate a route between two nodes
SELECT * FROM find_multimodal_route('generic_1', 'generic_100', TRUE);

-- Or use coordinates (with auto-snapping)
SELECT * FROM route_by_coordinates(5.0, 52.0, 10.0, 48.0, TRUE, 200.0);
```

### 5. Access via API

The routing endpoints are now available via FastAPI:

```bash
# Start the FastAPI server
cd fastapi
uvicorn app.main:app --reload

# Open the API documentation
# Navigate to: http://localhost:8000/docs
```

## Available API Endpoints

All routing endpoints are under `/api/v1/routing`:

### Route Calculation
- **GET** `/routing/route/coordinates` - Calculate route between lat/lon coordinates
- **GET** `/routing/route/nodes` - Calculate route between specific node IDs
- **GET** `/routing/route/summary` - Get route statistics summary
- **GET** `/routing/route/analyze` - Analyze route by transport mode

### Node Discovery
- **GET** `/routing/nodes/nearest` - Find nearest nodes to coordinates
- **GET** `/routing/terminals/nearest` - Find nearest LNG terminals
- **GET** `/routing/terminals/connections` - Get all terminal connectivity info

### Topology Management
- **POST** `/routing/topology/refresh` - Refresh routing topology
- **POST** `/routing/terminals/connect` - Create/update terminal connections

## Example API Usage

### Calculate a Multimodal Route

```bash
curl -X GET "http://localhost:8000/api/v1/routing/route/coordinates?start_lon=5.0&start_lat=52.0&end_lon=10.0&end_lat=48.0&allow_shipping=true&max_snap_km=200"
```

Response:
```json
{
  "route": [
    {
      "seq": 1,
      "path_node": "generic_123",
      "node_name": "Amsterdam Hub",
      "node_type": "generic",
      "edge_id": null,
      "edge_type": null,
      "segment_cost": null,
      "cumulative_cost": 0.0,
      "segment_km": null
    },
    {
      "seq": 2,
      "path_node": "generic_456",
      "node_name": "Rotterdam Junction",
      "node_type": "generic",
      "edge_id": "pipeline_789",
      "edge_type": "pipeline",
      "segment_cost": 0.2709,
      "cumulative_cost": 0.2709,
      "segment_km": 150.5
    },
    ...
  ],
  "snap_info": {
    "start_node_id": "generic_123",
    "start_node_type": "generic",
    "end_node_id": "generic_999",
    "end_node_type": "generic",
    "start_snap_km": 15.2,
    "end_snap_km": 22.8,
    "multimodal": true
  },
  "total_distance_km": 850.3,
  "total_cost": 1.5309
}
```

### Find Nearest Nodes

```bash
curl -X GET "http://localhost:8000/api/v1/routing/nodes/nearest?lon=5.0&lat=52.0&max_dist_km=100&node_types=generic,lng_terminal"
```

### Get Terminal Connectivity

```bash
curl -X GET "http://localhost:8000/api/v1/routing/terminals/connections"
```

Response:
```json
[
  {
    "terminal_id": 1,
    "terminal_name": "Zeebrugge LNG",
    "country_code": "BE",
    "capacity_m3_per_d": 15000000,
    "pipeline_connections": 5,
    "shipping_connections": 3,
    "total_connections": 8
  },
  ...
]
```

### Refresh Topology After Data Changes

```bash
curl -X POST "http://localhost:8000/api/v1/routing/topology/refresh"

# Then reconnect terminals with custom distances
curl -X POST "http://localhost:8000/api/v1/routing/terminals/connect?max_pipeline_km=75&max_shipping_km=150"
```

## Frontend Integration Example

```javascript
// Calculate route between two points
async function calculateRoute(startLon, startLat, endLon, endLat, allowShipping = true) {
  const response = await fetch(
    `/api/v1/routing/route/coordinates?` +
    `start_lon=${startLon}&start_lat=${startLat}&` +
    `end_lon=${endLon}&end_lat=${endLat}&` +
    `allow_shipping=${allowShipping}`
  );
  
  const data = await response.json();
  return data;
}

// Find nearest network access point
async function findNearestNode(lon, lat, maxDistKm = 200) {
  const response = await fetch(
    `/api/v1/routing/nodes/nearest?lon=${lon}&lat=${lat}&max_dist_km=${maxDistKm}`
  );
  
  const nodes = await response.json();
  return nodes[0]; // Return closest node
}

// Get all LNG terminals (for map markers)
async function getLngTerminals() {
  const response = await fetch(`/api/v1/routing/terminals/connections`);
  const terminals = await response.json();
  
  // Filter to only terminals with connections
  return terminals.filter(t => t.total_connections > 0);
}

// Example: Display route on map
async function displayRoute() {
  const route = await calculateRoute(5.0, 52.0, 10.0, 48.0, true);
  
  console.log(`Route found with ${route.route.length} segments`);
  console.log(`Total distance: ${route.total_distance_km} km`);
  console.log(`Total cost: ${route.total_cost}`);
  
  // Draw route on map (pseudo-code)
  route.route.forEach(segment => {
    if (segment.edge_type === 'pipeline') {
      drawPipelineSegment(segment, 'blue');
    } else if (segment.edge_type === 'shipping') {
      drawShippingSegment(segment, 'red');
    } else if (segment.node_type === 'lng_terminal') {
      addTerminalMarker(segment, 'yellow');
    }
  });
}
```

## Troubleshooting

### "No route found"
1. Check if nodes exist in the area:
   ```sql
   SELECT COUNT(*) FROM unified_nodes 
   WHERE ST_DWithin(geom::geography, ST_SetSRID(ST_Point(lon, lat), 4326)::geography, 200000);
   ```

2. Verify terminal connections exist:
   ```sql
   SELECT COUNT(*) FROM temp_terminal_edges;
   ```
   If 0, run: `SELECT * FROM create_terminal_connections();`

3. Try increasing `max_snap_km` parameter

### "Function does not exist"
- Ensure the SQL file was executed successfully
- Check for errors in the PostgreSQL logs
- Verify PostGIS and pgRouting extensions are installed:
  ```sql
  SELECT * FROM pg_extension WHERE extname IN ('postgis', 'pgrouting');
  ```

### Routing is slow
1. Refresh materialized views:
   ```sql
   SELECT refresh_routing_topology();
   ```

2. Check if indexes exist:
   ```sql
   SELECT indexname FROM pg_indexes WHERE tablename IN ('unified_nodes', 'unified_edges');
   ```

3. Analyze tables:
   ```sql
   ANALYZE unified_nodes;
   ANALYZE unified_edges;
   ```

### Terminal connections seem wrong
Adjust connection distances based on your network density:

```sql
-- For sparse networks, increase distances
SELECT * FROM create_terminal_connections(100.0, 200.0);

-- For dense networks, decrease distances
SELECT * FROM create_terminal_connections(25.0, 50.0);
```

## Maintenance

### After Adding New Data

Always run after adding pipeline segments, shipping lanes, or terminals:

```sql
-- 1. Refresh topology
SELECT refresh_routing_topology();

-- 2. Recreate terminal connections
SELECT * FROM create_terminal_connections();
```

Or via API:
```bash
curl -X POST "http://localhost:8000/api/v1/routing/topology/refresh"
curl -X POST "http://localhost:8000/api/v1/routing/terminals/connect"
```

### Monitoring Performance

```sql
-- Check materialized view sizes
SELECT 
    schemaname,
    matviewname,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||matviewname)) AS size
FROM pg_matviews
WHERE matviewname IN ('unified_nodes', 'unified_edges', 'shipping_lane_endpoints');

-- Check node/edge counts
SELECT 'Nodes' AS type, COUNT(*) AS count FROM unified_nodes
UNION ALL
SELECT 'Edges', COUNT(*) FROM unified_edges
UNION ALL
SELECT 'Terminal Connections', COUNT(*) FROM temp_terminal_edges;
```

## Next Steps

1. **Customize Costs**: Modify cost formulas in the `unified_edges` view to match your business logic
2. **Add Constraints**: Filter routes by capacity, diameter, or other pipeline properties
3. **Implement Caching**: Cache frequently requested routes for better performance
4. **Add Visualization**: Use the geometry columns to render routes on interactive maps
5. **Capacity Analysis**: Extend routing to consider flow capacity constraints

## Support

For issues or questions:
- Check the [MULTIMODAL_ROUTING_README.md](MULTIMODAL_ROUTING_README.md) for detailed function documentation
- Review the SQL file: `alembic/sql/multimodal_routing_functions.sql`
- Inspect the API endpoints: `app/api/v1/endpoints/routing.py`
