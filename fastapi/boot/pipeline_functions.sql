-- =============================================================
-- Pipeline Infrastructure: Functions, Views, and Seed Data
-- Run this AFTER Alembic migration creates the tables
-- Usage: python manage.py run-sql ext_scripts/002_pipeline_functions.sql
-- =============================================================

-- Ensure PostGIS and pgRouting extensions are enabled
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS pgrouting;

-- =============================================================
-- SEED DATA: Tariff Rules
-- Known ENTSOG reference values + fallback estimates
-- =============================================================
INSERT INTO tariff_rules (rule_name, country, tariff_type, eur_per_mwh_per_100km, fixed_entry_eur_mwh, source, notes) VALUES
('EU average distance-based',   NULL, 'distance_based', 0.18, NULL,  'ENTSOG CAM NP 2023', 'Rough EU average, use as fallback'),
('Germany regulated',           'DE', 'regulated',      0.22, 0.15,  'BNetzA 2023',        'German entry-exit tariff'),
('Netherlands regulated',       'NL', 'regulated',      0.14, 0.10,  'ACM 2023',           'Dutch TSO tariff'),
('France regulated',            'FR', 'regulated',      0.19, 0.12,  'CRE 2023',           'French GRTgaz tariff'),
('Belgium regulated',           'BE', 'regulated',      0.16, 0.11,  'CREG 2023',          'Belgian Fluxys tariff'),
('UK regulated',                'GB', 'regulated',      0.17, 0.13,  'Ofgem 2023',         'UK NGG tariff'),
('Norway offshore',             'NO', 'negotiated',     0.25, NULL,  'Estimated',          'Gassled tariff estimate'),
('Algeria Medgaz',              'DZ', 'fixed_entry',    NULL, 0.45,  'Estimated 2023',     'Algeria-Spain submarine tariff estimate'),
('Algeria Transmed',            'DZ', 'fixed_entry',    NULL, 0.52,  'Estimated 2023',     'Algeria-Italy tariff estimate')
ON CONFLICT DO NOTHING;

-- =============================================================
-- FUNCTION: recompute_edge_costs()
-- Compute and update cost_composite for all edges
-- Call this after loading pipeline data or updating tariff rules
-- =============================================================
CREATE OR REPLACE FUNCTION recompute_edge_costs()
RETURNS void LANGUAGE plpgsql AS $$
BEGIN
    -- Step 1: fill distance_km from geometry where missing
    UPDATE pipeline_edges
    SET cost_distance_km = ROUND(
        (ST_Length(geom::geography) / 1000.0)::NUMERIC, 3
    )
    WHERE geom IS NOT NULL
      AND (cost_distance_km IS NULL OR cost_distance_km = 0);

    -- Mirror distance as reverse where pipeline is bidirectional
    UPDATE pipeline_edges
    SET reverse_cost_distance_km = cost_distance_km
    WHERE reverse_cost_distance_km IS NULL
      AND cost_distance_km IS NOT NULL;

    -- Step 2: estimate tariff from rules where real tariff missing
    UPDATE pipeline_edges e
    SET cost_tariff_eur_mwh = ROUND(
        COALESCE(
            -- Use country-specific rule if available
            (SELECT r.eur_per_mwh_per_100km * e.cost_distance_km / 100.0
               + COALESCE(r.fixed_entry_eur_mwh, 0)
             FROM tariff_rules r
             WHERE r.country = ANY(e.country_codes)
             ORDER BY r.country NULLS LAST LIMIT 1),
            -- Fall back to global average
            (SELECT r.eur_per_mwh_per_100km * e.cost_distance_km / 100.0
             FROM tariff_rules r WHERE r.country IS NULL LIMIT 1)
        )::NUMERIC, 4
    )
    WHERE cost_tariff_eur_mwh IS NULL
      AND cost_distance_km IS NOT NULL;

    UPDATE pipeline_edges
    SET reverse_cost_tariff_eur_mwh = cost_tariff_eur_mwh
    WHERE reverse_cost_tariff_eur_mwh IS NULL;

    -- Step 3: composite = tariff where available, else distance-based estimate
    UPDATE pipeline_edges
    SET cost_composite = COALESCE(
        cost_tariff_eur_mwh,
        cost_distance_km * 0.0018  -- 0.18 €/MWh per 100km → per km
    );

    UPDATE pipeline_edges
    SET reverse_cost_composite = COALESCE(
        reverse_cost_tariff_eur_mwh,
        reverse_cost_distance_km * 0.0018
    );

    -- Decommissioned/planned edges get -1 (disabled in pgRouting)
    UPDATE pipeline_edges
    SET cost_composite = -1,
        reverse_cost_composite = -1
    WHERE status NOT IN ('operating', 'construction');

    RAISE NOTICE 'Edge costs recomputed for % edges',
        (SELECT COUNT(*) FROM pipeline_edges WHERE cost_composite > 0);
END;
$$;

-- =============================================================
-- VIEW: pipeline_routing_graph
-- Clean interface for pgRouting — always uses cost_composite
-- pgRouting needs: id, source, target, cost, reverse_cost
-- =============================================================
CREATE OR REPLACE VIEW pipeline_routing_graph AS
SELECT
    id,
    source,
    target,
    cost_composite          AS cost,
    reverse_cost_composite  AS reverse_cost
FROM pipeline_edges
WHERE status IN ('operating', 'construction');  -- exclude retired/planned

-- =============================================================
-- FUNCTION: nearest_node()
-- Find the nearest pipeline node to a given coordinate
-- =============================================================
CREATE OR REPLACE FUNCTION nearest_node(
    lon FLOAT,
    lat FLOAT,
    max_dist_km FLOAT DEFAULT 200.0,
    node_types TEXT[] DEFAULT NULL   -- NULL = any type
)
RETURNS TABLE (
    node_id     BIGINT,
    name        TEXT,
    node_type   TEXT,
    distance_km NUMERIC
) LANGUAGE sql STABLE AS $$
    SELECT
        id,
        name,
        node_type,
        ROUND((ST_Distance(
            geom::geography,
            ST_SetSRID(ST_Point(lon, lat), 4326)::geography
        ) / 1000.0)::NUMERIC, 2) AS distance_km
    FROM pipeline_nodes
    WHERE
        status = 'operating'
        AND ST_DWithin(
            geom::geography,
            ST_SetSRID(ST_Point(lon, lat), 4326)::geography,
            max_dist_km * 1000   -- metres
        )
        AND (node_types IS NULL OR node_type = ANY(node_types))
    ORDER BY geom <-> ST_SetSRID(ST_Point(lon, lat), 4326)
    LIMIT 5;
$$;

-- =============================================================
-- FUNCTION: find_cheapest_gas_route()
-- Find the cheapest path between two nodes using pgRouting
-- =============================================================
CREATE OR REPLACE FUNCTION find_cheapest_gas_route(
    start_node_id   BIGINT,
    end_node_id     BIGINT,
    cost_column     TEXT DEFAULT 'composite'   -- 'composite' | 'tariff' | 'distance'
)
RETURNS TABLE (
    seq             INT,
    node_id         BIGINT,
    node_name       TEXT,
    edge_id         BIGINT,
    pipeline_name   TEXT,
    segment_cost    NUMERIC,
    cumulative_cost NUMERIC,
    segment_km      NUMERIC,
    geom            GEOMETRY
) LANGUAGE plpgsql STABLE AS $$
DECLARE
    cost_col    TEXT;
    rcost_col   TEXT;
    edges_sql   TEXT;
BEGIN
    -- Select which cost column to optimise
    cost_col  := CASE cost_column
        WHEN 'tariff'   THEN 'COALESCE(cost_tariff_eur_mwh, cost_composite)'
        WHEN 'distance' THEN 'cost_distance_km'
        ELSE 'cost_composite'
    END;
    rcost_col := CASE cost_column
        WHEN 'tariff'   THEN 'COALESCE(reverse_cost_tariff_eur_mwh, reverse_cost_composite)'
        WHEN 'distance' THEN 'reverse_cost_distance_km'
        ELSE 'reverse_cost_composite'
    END;

    edges_sql := format(
        'SELECT id, source, target, %s AS cost, %s AS reverse_cost
         FROM pipeline_edges
         WHERE status IN (''operating'', ''construction'')',
        cost_col, rcost_col
    );

    RETURN QUERY
    SELECT
        d.seq::INT,
        n.id            AS node_id,
        n.name          AS node_name,
        e.id            AS edge_id,
        e.pipeline_name,
        ROUND(d.cost::NUMERIC, 4)           AS segment_cost,
        ROUND(d.agg_cost::NUMERIC, 4)       AS cumulative_cost,
        ROUND(e.cost_distance_km, 2)        AS segment_km,
        e.geom
    FROM pgr_dijkstra(edges_sql, start_node_id, end_node_id, TRUE) d
    LEFT JOIN pipeline_nodes n ON n.id = d.node
    LEFT JOIN pipeline_edges e ON e.id = d.edge
    ORDER BY d.seq;
END;
$$;

-- =============================================================
-- FUNCTION: route_by_coordinates()
-- Route between two lon/lat points (snaps to nearest nodes)
-- =============================================================
CREATE OR REPLACE FUNCTION route_by_coordinates(
    start_lon   FLOAT,
    start_lat   FLOAT,
    end_lon     FLOAT,
    end_lat     FLOAT,
    cost_column TEXT DEFAULT 'composite',
    max_snap_km FLOAT DEFAULT 200.0
)
RETURNS TABLE (
    seq             INT,
    node_id         BIGINT,
    node_name       TEXT,
    edge_id         BIGINT,
    pipeline_name   TEXT,
    segment_cost    NUMERIC,
    cumulative_cost NUMERIC,
    segment_km      NUMERIC,
    geom            GEOMETRY,
    snap_info       JSON
) LANGUAGE plpgsql STABLE AS $$
DECLARE
    start_id    BIGINT;
    end_id      BIGINT;
    start_dist  NUMERIC;
    end_dist    NUMERIC;
BEGIN
    -- Snap start point to nearest node
    SELECT n.node_id, n.distance_km INTO start_id, start_dist
    FROM nearest_node(start_lon, start_lat, max_snap_km) n
    LIMIT 1;

    -- Snap end point to nearest node
    SELECT n.node_id, n.distance_km INTO end_id, end_dist
    FROM nearest_node(end_lon, end_lat, max_snap_km) n
    LIMIT 1;

    IF start_id IS NULL THEN
        RAISE EXCEPTION 'No pipeline node within %km of start point (%, %)',
            max_snap_km, start_lon, start_lat;
    END IF;
    IF end_id IS NULL THEN
        RAISE EXCEPTION 'No pipeline node within %km of end point (%, %)',
            max_snap_km, end_lon, end_lat;
    END IF;

    RETURN QUERY
    SELECT
        r.*,
        json_build_object(
            'start_node_id', start_id,
            'end_node_id', end_id,
            'start_snap_km', start_dist,
            'end_snap_km', end_dist
        ) AS snap_info
    FROM find_cheapest_gas_route(start_id, end_id, cost_column) r;
END;
$$;

-- Pipeline functions and views created successfully
