# Simple Pipeline Routing

## Quick Start

### 1. Run the SQL file

```bash
psql -d your_database -f alembic/sql/simple_routing.sql
```

### 2. Find a route between two nodes

```sql
-- Find shortest path between node 1 and node 100
SELECT * FROM find_shortest_path(1, 100);
```

Result:
```
 seq | node_id | node_name        | edge_id | distance_km | total_distance
-----+---------+------------------+---------+-------------+----------------
   1 |       1 | Amsterdam Hub    |         |             |           0.00
   2 |      23 | Rotterdam        |     456 |      150.50 |         150.50
   3 |      45 | Antwerp          |     789 |       80.20 |         230.70
   4 |     100 | Brussels         |     234 |      120.00 |         350.70
```

## Functions

### find_shortest_path(start_node_id, end_node_id)
Find the shortest route between two nodes by distance.

```sql
SELECT * FROM find_shortest_path(1, 100);
```

### get_node_neighbors(node_id)
Get all nodes directly connected to a node.

```sql
SELECT * FROM get_node_neighbors(1);
```

### check_nodes_connected(node_a, node_b)
Check if a path exists between two nodes.

```sql
SELECT check_nodes_connected(1, 100);  -- Returns TRUE/FALSE
```

### get_route_summary(start_node_id, end_node_id)
Get basic statistics about a route.

```sql
SELECT * FROM get_route_summary(1, 100);
```

Result:
```
 start_node | end_node | total_distance | segment_count | node_count
------------+----------+----------------+---------------+------------
          1 |      100 |         350.70 |             3 |          4
```

## Recommendation: Consolidate Node Tables

**Current structure** (3 separate tables):
- `generic_nodes` - regular nodes
- `border_nodes` - border crossings
- `lng_terminals` - LNG terminals

**Recommended structure** (1 unified table):

```sql
CREATE TABLE nodes (
    id BIGINT PRIMARY KEY,
    name TEXT,
    geom GEOMETRY(POINT, 4326),
    country_code VARCHAR(2),
    
    -- Type flags
    is_border_node BOOLEAN DEFAULT FALSE,
    is_lng_terminal BOOLEAN DEFAULT FALSE,
    
    -- Border node specific (nullable)
    from_country VARCHAR(2),
    to_country VARCHAR(2),
    from_TSO TEXT,
    to_TSO TEXT,
    
    -- LNG terminal specific (nullable)
    capacity_m3_per_d NUMERIC,
    start_year INTEGER,
    
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP
);

-- Index for different node types
CREATE INDEX idx_nodes_border ON nodes(is_border_node) WHERE is_border_node = TRUE;
CREATE INDEX idx_nodes_lng ON nodes(is_lng_terminal) WHERE is_lng_terminal = TRUE;
CREATE INDEX idx_nodes_geom ON nodes USING GIST(geom);
```

### Benefits:
1. **Simpler routing** - one table to query, no UNIONs needed
2. **Easier foreign keys** - `pipeline_segments` just references `nodes.id`
3. **Single ID sequence** - no conflicts between node types
4. **Flexible queries** - easy to filter by type with WHERE clause
5. **Better performance** - fewer JOINs, simpler query plans

### Migration Example:

```sql
-- 1. Create new unified nodes table
CREATE TABLE nodes AS
SELECT 
    id,
    name,
    geom,
    country_code,
    FALSE as is_border_node,
    FALSE as is_lng_terminal,
    NULL::VARCHAR(2) as from_country,
    NULL::VARCHAR(2) as to_country,
    NULL::TEXT as from_TSO,
    NULL::TEXT as to_TSO,
    NULL::NUMERIC as capacity_m3_per_d,
    NULL::INTEGER as start_year,
    created_at,
    updated_at
FROM generic_nodes

UNION ALL

SELECT 
    id,
    name,
    geom,
    country_code,
    TRUE as is_border_node,
    FALSE as is_lng_terminal,
    from_country,
    to_country,
    from_TSO,
    to_TSO,
    NULL::NUMERIC as capacity_m3_per_d,
    NULL::INTEGER as start_year,
    created_at,
    updated_at
FROM border_nodes

UNION ALL

SELECT 
    id,
    name,
    geom,
    country_code,
    FALSE as is_border_node,
    TRUE as is_lng_terminal,
    NULL::VARCHAR(2) as from_country,
    NULL::VARCHAR(2) as to_country,
    from_TSO,
    to_TSO,
    max_cap_store2pipe_M_m3_per_d * 1000000 as capacity_m3_per_d,
    start_year,
    created_at,
    updated_at
FROM lng_terminals;

-- 2. Add constraints and indexes
ALTER TABLE nodes ADD PRIMARY KEY (id);
CREATE INDEX idx_nodes_border ON nodes(is_border_node) WHERE is_border_node = TRUE;
CREATE INDEX idx_nodes_lng ON nodes(is_lng_terminal) WHERE is_lng_terminal = TRUE;
CREATE INDEX idx_nodes_geom ON nodes USING GIST(geom);

-- 3. Update pipeline_segments to use the new table
-- (no changes needed if IDs are preserved)

-- 4. Drop old tables (after verifying everything works)
-- DROP TABLE generic_nodes;
-- DROP TABLE border_nodes;
-- DROP TABLE lng_terminals;
```

## Usage Examples

### Basic Routing
```sql
-- Find path
SELECT * FROM find_shortest_path(1, 100);

-- Check if path exists first
SELECT check_nodes_connected(1, 100);

-- Get summary
SELECT * FROM get_route_summary(1, 100);
```

### Network Analysis
```sql
-- Find all neighbors of a node
SELECT * FROM get_node_neighbors(1);

-- Find nodes with most connections
SELECT 
    node_id,
    COUNT(*) as connection_count
FROM (
    SELECT DISTINCT from_node_id as node_id FROM pipeline_segments
    UNION ALL
    SELECT DISTINCT to_node_id FROM pipeline_segments
) nodes
GROUP BY node_id
ORDER BY connection_count DESC
LIMIT 10;
```

### Using with Unified Nodes Table
```sql
-- Find path between two LNG terminals
SELECT r.*, n.is_lng_terminal
FROM find_shortest_path(
    (SELECT id FROM nodes WHERE is_lng_terminal = TRUE LIMIT 1),
    (SELECT id FROM nodes WHERE is_lng_terminal = TRUE OFFSET 1 LIMIT 1)
) r
LEFT JOIN nodes n ON n.id = r.node_id;

-- Find shortest path that crosses a border
SELECT * FROM find_shortest_path(
    (SELECT id FROM nodes WHERE country_code = 'NL' LIMIT 1),
    (SELECT id FROM nodes WHERE country_code = 'DE' LIMIT 1)
);
```
