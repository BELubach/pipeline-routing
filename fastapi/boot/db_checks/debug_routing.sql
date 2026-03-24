
-- 1. Check if we have nodes in the Netherlands bbox
SELECT COUNT(*) as node_count
FROM pipeline_nodes
WHERE ST_Contains(
    ST_MakeEnvelope(3.0, 50.0, 7.5, 54.0, 4326),
    geom
);

-- 2. Check if we have edges
SELECT COUNT(*) as edge_count FROM pipeline_edges;

-- 3. Check edge cost columns (are they NULL?)
SELECT 
    COUNT(*) as total_edges,
    COUNT(cost_distance_km) as has_distance,
    COUNT(cost_tariff_eur_mwh) as has_tariff,
    COUNT(cost_composite) as has_composite,
    AVG(cost_distance_km) as avg_distance_km,
    AVG(cost_composite) as avg_composite
FROM pipeline_edges;

-- 4. Sample edges to see their data
SELECT 
    id,
    source,
    target,
    pipeline_name,
    cost_distance_km,
    cost_composite,
    ST_AsText(ST_StartPoint(geom)) as start_pt,
    ST_AsText(ST_EndPoint(geom)) as end_pt
FROM pipeline_edges
LIMIT 5;

-- 5. Find nodes near Groningen coordinates (6.83, 53.4)
SELECT 
    id,
    name,
    node_type,
    ST_Distance(
        geom::geography,
        ST_SetSRID(ST_Point(6.83, 53.4), 4326)::geography
    ) / 1000.0 AS distance_km
FROM pipeline_nodes
WHERE ST_DWithin(
    geom::geography,
    ST_SetSRID(ST_Point(6.83, 53.4), 4326)::geography,
    200000  -- 200km in meters
)
ORDER BY geom <-> ST_SetSRID(ST_Point(6.83, 53.4), 4326)
LIMIT 5;

-- 6. Test if nearest_node function works
SELECT * FROM nearest_node(6.83, 53.4, 200, NULL);

-- 7. Check if pgRouting can find a path between two specific nodes
-- First find two nearby nodes
WITH nearby_nodes AS (
    SELECT id
    FROM pipeline_nodes
    WHERE ST_DWithin(
        geom::geography,
        ST_SetSRID(ST_Point(6.83, 53.4), 4326)::geography,
        50000  -- 50km
    )
    ORDER BY geom <-> ST_SetSRID(ST_Point(6.83, 53.4), 4326)
    LIMIT 2
)
SELECT 
    id,
    (SELECT ARRAY_AGG(id) FROM nearby_nodes) as node_ids,
    'Check if these nodes can route' as note
FROM nearby_nodes;
