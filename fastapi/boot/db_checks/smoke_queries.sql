-- =============================================================
-- Smoke tests & useful example queries
-- Run these after importing data to verify the setup
-- =============================================================

-- 1. Check extensions loaded
SELECT name, default_version, installed_version
FROM pg_available_extensions
WHERE name IN ('postgis', 'pgrouting');

-- 2. Node and edge counts
SELECT 'nodes' AS table, COUNT(*) FROM pipeline_nodes
UNION ALL
SELECT 'edges', COUNT(*) FROM pipeline_edges
UNION ALL
SELECT 'edges_operating', COUNT(*) FROM pipeline_edges WHERE status = 'operating';

-- 3. Cost column coverage
SELECT
    COUNT(*) AS total_edges,
    COUNT(cost_distance_km) AS have_distance,
    COUNT(cost_tariff_eur_mwh) AS have_tariff,
    COUNT(cost_composite) AS have_composite,
    COUNT(*) FILTER (WHERE cost_composite < 0) AS disabled_edges
FROM pipeline_edges;

-- 4. Find nearest node to Amsterdam (lon=4.9, lat=52.37)
SELECT * FROM nearest_node(4.9, 52.37, 300);

-- 5. Route from Emden entry (Norwegian gas entry into Germany)
--    to Baumgarten hub (Austria) — major physical flow
SELECT
    seq, node_name, pipeline_name,
    segment_cost AS cost_eur_mwh,
    cumulative_cost AS total_eur_mwh,
    segment_km
FROM find_cheapest_gas_route(
    (SELECT id FROM pipeline_nodes WHERE name LIKE '%Emden%' LIMIT 1),
    (SELECT id FROM pipeline_nodes WHERE name LIKE '%Baumgarten%' LIMIT 1),
    'composite'
);

-- 6. Route by raw coordinates:
--    Emden area (7.2, 53.4) → Vienna (16.4, 48.2)
SELECT seq, node_name, pipeline_name, segment_cost, cumulative_cost, segment_km
FROM route_by_coordinates(7.2, 53.4, 16.4, 48.2);

-- 7. What nodes can be reached from TTF hub within €2/MWh transport cost?
--    (This is the ChronoTrains equivalent)
SELECT
    n.name, n.node_type, n.country,
    ROUND(dd.agg_cost::NUMERIC, 3) AS cost_eur_mwh
FROM pgr_drivingDistance(
    'SELECT id, source, target,
            cost_composite AS cost,
            reverse_cost_composite AS reverse_cost
     FROM pipeline_edges
     WHERE status IN (''operating'', ''construction'')',
    (SELECT id FROM pipeline_nodes WHERE hub_code = 'TTF' LIMIT 1),
    2.0,        -- max cost budget
    directed := true
) dd
JOIN pipeline_nodes n ON n.id = dd.node
WHERE dd.agg_cost > 0
ORDER BY dd.agg_cost;

-- 8. Graph connectivity check — are there any isolated nodes?
WITH connected AS (
    SELECT DISTINCT source AS node_id FROM pipeline_edges WHERE cost_composite > 0
    UNION
    SELECT DISTINCT target FROM pipeline_edges WHERE cost_composite > 0
)
SELECT n.id, n.name, n.node_type
FROM pipeline_nodes n
LEFT JOIN connected c ON c.node_id = n.id
WHERE c.node_id IS NULL
  AND n.status = 'operating';

-- 9. Most expensive pipeline segments (potential bottlenecks)
SELECT pipeline_name, country_codes,
       ROUND(cost_composite::NUMERIC, 4) AS cost_eur_mwh,
       ROUND(cost_distance_km::NUMERIC, 1) AS km
FROM pipeline_edges
WHERE cost_composite > 0
ORDER BY cost_composite DESC
LIMIT 20;

-- 10. Tariff coverage by pipeline
SELECT
    pipeline_name,
    tariff_type,
    tariff_source,
    COUNT(*) AS segment_count,
    AVG(cost_composite)::NUMERIC(6,4) AS avg_cost_eur_mwh
FROM pipeline_edges
WHERE cost_composite > 0
GROUP BY pipeline_name, tariff_type, tariff_source
ORDER BY avg_cost_eur_mwh DESC
LIMIT 30;
