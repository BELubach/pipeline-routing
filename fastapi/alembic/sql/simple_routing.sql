-- =============================================================
-- Simple Pipeline Routing
-- Basic shortest path routing for pipeline network
-- =============================================================

-- Ensure PostGIS and pgRouting extensions are enabled
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS pgrouting;

-- =============================================================
-- FUNCTION: find_shortest_path()
-- Find the shortest path between two nodes by distance
-- Simple distance-based routing, no cost calculations
-- =============================================================
CREATE OR REPLACE FUNCTION find_shortest_path(
    start_node_id BIGINT,
    end_node_id BIGINT
)
RETURNS TABLE (
    seq             INT,
    node_id         BIGINT,
    node_name       TEXT,
    edge_id         BIGINT,
    distance_km     NUMERIC,
    total_distance  NUMERIC
) LANGUAGE plpgsql STABLE AS $$
BEGIN
    RETURN QUERY
    WITH route AS (
        SELECT * FROM pgr_dijkstra(
            'SELECT id, 
                    CAST(from_node_id AS BIGINT) as source, 
                    CAST(to_node_id AS BIGINT) as target,
                    length_km as cost,
                    length_km as reverse_cost
             FROM pipeline_segments
             WHERE from_node_id IS NOT NULL 
               AND to_node_id IS NOT NULL',
            start_node_id,
            end_node_id,
            directed := false
        ) r
    )
    SELECT
        r.seq::INT,
        r.node::BIGINT AS node_id,
        gn.name AS node_name,
        r.edge::BIGINT AS edge_id,
        ps.length_km AS distance_km,
        ROUND(r.agg_cost::NUMERIC, 2) AS total_distance
    FROM route r
    LEFT JOIN generic_nodes gn ON gn.id = r.node
    LEFT JOIN pipeline_segments ps ON ps.id = r.edge
    ORDER BY r.seq;
END;
$$;

-- =============================================================
-- FUNCTION: get_node_neighbors()
-- Get all nodes directly connected to a given node
-- Useful for understanding network connectivity
-- =============================================================
CREATE OR REPLACE FUNCTION get_node_neighbors(node_id BIGINT)
RETURNS TABLE (
    neighbor_id     BIGINT,
    neighbor_name   TEXT,
    distance_km     NUMERIC,
    segment_id      BIGINT
) LANGUAGE sql STABLE AS $$
    -- Outgoing connections
    SELECT 
        CAST(ps.to_node_id AS BIGINT) AS neighbor_id,
        gn.name AS neighbor_name,
        ps.length_km AS distance_km,
        ps.id AS segment_id
    FROM pipeline_segments ps
    LEFT JOIN generic_nodes gn ON gn.id = CAST(ps.to_node_id AS BIGINT)
    WHERE CAST(ps.from_node_id AS BIGINT) = node_id
    
    UNION
    
    -- Incoming connections (since pipelines are bidirectional)
    SELECT 
        CAST(ps.from_node_id AS BIGINT) AS neighbor_id,
        gn.name AS neighbor_name,
        ps.length_km AS distance_km,
        ps.id AS segment_id
    FROM pipeline_segments ps
    LEFT JOIN generic_nodes gn ON gn.id = CAST(ps.from_node_id AS BIGINT)
    WHERE CAST(ps.to_node_id AS BIGINT) = node_id;
$$;

-- =============================================================
-- FUNCTION: check_nodes_connected()
-- Check if two nodes are in the same connected component
-- Returns TRUE if a path exists between them
-- =============================================================
CREATE OR REPLACE FUNCTION check_nodes_connected(
    node_a BIGINT,
    node_b BIGINT
)
RETURNS BOOLEAN LANGUAGE plpgsql STABLE AS $$
DECLARE
    path_exists BOOLEAN;
BEGIN
    SELECT EXISTS (
        SELECT 1 FROM pgr_dijkstra(
            'SELECT id, 
                    CAST(from_node_id AS BIGINT) as source, 
                    CAST(to_node_id AS BIGINT) as target,
                    length_km as cost,
                    length_km as reverse_cost
             FROM pipeline_segments
             WHERE from_node_id IS NOT NULL 
               AND to_node_id IS NOT NULL',
            node_a,
            node_b,
            directed := false
        ) r
        WHERE r.edge != -1  -- -1 indicates no path found
    ) INTO path_exists;
    
    RETURN path_exists;
END;
$$;

-- =============================================================
-- FUNCTION: get_route_summary()
-- Get basic statistics about a route
-- =============================================================
CREATE OR REPLACE FUNCTION get_route_summary(
    start_node_id BIGINT,
    end_node_id BIGINT
)
RETURNS TABLE (
    start_node      BIGINT,
    end_node        BIGINT,
    total_distance  NUMERIC,
    segment_count   BIGINT,
    node_count      BIGINT
) LANGUAGE sql STABLE AS $$
    WITH route AS (
        SELECT * FROM find_shortest_path(start_node_id, end_node_id)
    )
    SELECT
        start_node_id AS start_node,
        end_node_id AS end_node,
        MAX(total_distance) AS total_distance,
        COUNT(*) FILTER (WHERE edge_id IS NOT NULL) AS segment_count,
        COUNT(*) AS node_count
    FROM route;
$$;

-- Success message
DO $$
BEGIN
    RAISE NOTICE '=============================================================';
    RAISE NOTICE 'Simple routing functions created successfully';
    RAISE NOTICE '=============================================================';
    RAISE NOTICE 'Available functions:';
    RAISE NOTICE '  - find_shortest_path(start_node_id, end_node_id)';
    RAISE NOTICE '  - get_node_neighbors(node_id)';
    RAISE NOTICE '  - check_nodes_connected(node_a, node_b)';
    RAISE NOTICE '  - get_route_summary(start_node_id, end_node_id)';
    RAISE NOTICE '=============================================================';
END;
$$;
