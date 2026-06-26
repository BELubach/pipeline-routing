
# Gas network routing model — system overview
 
## What we are modelling
 
The cost of transporting natural gas from any point on a **maritime shipping route** to any point in the **European pipeline network**, via an **LNG terminal** that regasifies the cargo and injects it into the grid.
 
The model answers: *"what is the cheapest path (in €/MWh) from ship origin X to pipeline delivery point Y, and which terminal should the cargo flow through?"*
 


Our spring batch script imported iggielgn generic nodes and lng_terminals. Each have unique iggielgn_ids, but if we run

``` sql 
SELECT
  t.id                AS terminal_id,
  t."IGGIELGN_id"     AS terminal_iggielgn_id,
  t.name              AS terminal_name,
  g.id                AS node_id,
  g."IGGIELGN_id"     AS node_iggielgn_id,
  g.name              AS node_name
FROM lng_terminals t
LEFT JOIN generic_nodes g ON ST_Equals(t.geom, g.geom)
ORDER BY g.id NULLS LAST;


-- returns 
 terminal_id | terminal_iggielgn_id |       terminal_name        | node_id | node_iggielgn_id |  node_name   
-------------+----------------------+----------------------------+---------+------------------+--------------
          18 | INET_LG_21           | Tallinn                    |     320 | N_757_M_LMGN     | N_757_M_LMGN
          13 | INET_LG_15           | Huelva                     |    1148 | INET_N_697       | INET_N_697
          25 | INET_LG_30           | Sines                      |    1738 | N_80_M_LMGN      | N_80_M_LMGN
           2 | INET_LG_3            | Bilbao                     |    1896 | N_340_M_LMGN     | N_340_M_LMGN
           7 | INET_LG_9            | Dunkerque                  |    3242 | N_3_NS_LMGN      | N_3_NS_LMGN
          30 | GIE_LG_16            | Porto Levante LNG Terminal |    4030 | SEQ_7584_p       | 
           1 | INET_LG_2            | Barcelona                  |    4031 | INET_N_142       | INET_N_142
          26 | INET_LG_31           | South Hook                 |    4032 | INET_N_1527      | INET_N_1527
          27 | INET_LG_32           | Swinoujscie                |    4034 | INET_N_1586      | INET_N_1586
           3 | INET_LG_5            | Cartagena                  |    4035 | INET_N_449       | INET_N_449
           9 | INET_LG_11           | Fos Cavaou                 |    4036 | INET_N_547       | INET_N_547
          11 | INET_LG_13           | Gate Rotterdam             |    4038 | INET_N_479       | INET_N_479
           4 | INET_LG_6            | Cavarzere                  |    4039 | INET_N_299       | INET_N_299
          16 | INET_LG_19           | Montoir De Bretagne        |    4040 | INET_N_1099      | INET_N_1099
          17 | INET_LG_20           | Mugardos                   |    4041 | INET_N_1112      | INET_N_1112
          23 | INET_LG_28           | Riga                       |    4042 | INET_N_1356      | INET_N_1356
          15 | INET_LG_17           | Klaipeda                   |    4043 | INET_N_847       | INET_N_847
           8 | INET_LG_10           | El Musel                   |    4044 | INET_N_461       | INET_N_461
          14 | INET_LG_16           | Isle Of Grain              |    4046 | INET_N_746       | INET_N_746
          12 | INET_LG_14           | Gothenburg                 |    4182 | INET_N_605       | INET_N_605
          19 | INET_LG_22           | Teesside                   |    4212 | INET_N_1616      | INET_N_1616
          20 | INET_LG_25           | Panigaglia                 |    4473 | INET_N_1231      | INET_N_1231
          29 | INET_LG_34           | Zeebrugge                  |    4606 | INET_N_1834      | INET_N_1834
          28 | INET_LG_33           | Toscana                    |    4607 | INET_N_1649      | INET_N_1649
           6 | INET_LG_8            | Dragon                     |    4608 | INET_N_1245      | INET_N_1245
          10 | INET_LG_12           | Fos Tonkin                 |    4609 | INET_N_546       | INET_N_546
          22 | INET_LG_27           | Revithoussa                |    4610 | INET_N_1351      | INET_N_1351
          24 | INET_LG_29           | Sagunto                    |    4611 | INET_N_1409      | INET_N_1409
           5 | INET_LG_7            | Delimara                   |    4673 | INET_N_379       | INET_N_379
          21 | INET_LG_26           | Pori                       |    4674 | INET_N_1287      | INET_N_1287
(30 rows)
```

So the ids are different, but the geometries have an exact match. We then use this to connect the IGGIELGN network to the maritime_routes.




We then create a new table to store the connection. Three foreign keys exist, the terminal, the nearest generic (iggielgn) node and the maritime route vertice (node). 

``` sql 
CREATE TABLE terminal_connections (
  id                  bigserial PRIMARY KEY,
  terminal_id         bigint NOT NULL REFERENCES lng_terminals(id),
  pipeline_node_id    bigint REFERENCES generic_nodes(id),
  shipping_node_id    bigint REFERENCES maritime_routes_vertices(id),   
  dist_to_pipeline_m  float,
  dist_to_shipping_m  float,
  snap_method         varchar(20) DEFAULT 'nearest',  -- 'nearest', 'exact', 'manual'
  connector_pipeline  geometry(LineString, 4326),     -- visual line terminal→pipeline node
  connector_shipping  geometry(LineString, 4326),     -- visual line terminal→shipping node
  created_at          timestamptz DEFAULT now()
);

-- index for spatial queries and FK lookups
CREATE INDEX ON terminal_connections (terminal_id);
CREATE INDEX ON terminal_connections (pipeline_node_id);
CREATE INDEX ON terminal_connections (shipping_node_id);
CREATE INDEX ON terminal_connections USING GIST (connector_pipeline);
CREATE INDEX ON terminal_connections USING GIST (connector_shipping);

```


``` sql 
INSERT INTO terminal_connections (
  terminal_id,
  pipeline_node_id,
  dist_to_pipeline_m,
  connector_pipeline,
  snap_method
)
SELECT
  t.id                                          AS terminal_id,
  n.id                                          AS pipeline_node_id,
  ST_Distance(
    ST_Transform(t.geom, 3857),
    ST_Transform(n.geom, 3857)
  )                                             AS dist_to_pipeline_m,
  ST_MakeLine(t.geom, n.geom)                   AS connector_pipeline,
  'nearest'                                     AS snap_method
FROM lng_terminals t
CROSS JOIN LATERAL (
  SELECT id, geom
  FROM   generic_nodes
  ORDER BY t.geom <-> geom     -- KNN, uses spatial index
  LIMIT  1
) n;
```



Check if the connection script worked

``` sql 
SELECT
  t.name                    AS terminal,
  g.name                    AS pipeline_node,
  ROUND(dist_to_pipeline_m) AS dist_m
FROM terminal_connections tc
JOIN lng_terminals  t ON t.id = tc.terminal_id
JOIN generic_nodes  g ON g.id = tc.pipeline_node_id
ORDER BY dist_m;


-- returns 
terminal          | pipeline_node | dist_m 
----------------------------+---------------+--------
 Barcelona                  | INET_N_142    |      0
 Bilbao                     | N_340_M_LMGN  |      0
 Cartagena                  | INET_N_449    |      0
 Cavarzere                  | INET_N_299    |      0
 Delimara                   | INET_N_379    |      0
 Dragon                     | INET_N_1245   |      0
 Dunkerque                  | N_3_NS_LMGN   |      0
 El Musel                   | INET_N_461    |      0
 Fos Cavaou                 | INET_N_547    |      0
 Fos Tonkin                 | INET_N_546    |      0
 Gate Rotterdam             | INET_N_479    |      0
 Gothenburg                 | INET_N_605    |      0
 Huelva                     | INET_N_697    |      0
 Isle Of Grain              | INET_N_746    |      0
 Klaipeda                   | INET_N_847    |      0
 Montoir De Bretagne        | INET_N_1099   |      0
 Mugardos                   | INET_N_1112   |      0
 Tallinn                    | N_757_M_LMGN  |      0
 Teesside                   | INET_N_1616   |      0
 Panigaglia                 | INET_N_1231   |      0
 Pori                       | INET_N_1287   |      0
 Revithoussa                | INET_N_1351   |      0
 Riga                       | INET_N_1356   |      0
 Sagunto                    | INET_N_1409   |      0
 Sines                      | N_80_M_LMGN   |      0
 South Hook                 | INET_N_1527   |      0
 Swinoujscie                | INET_N_1586   |      0
 Toscana                    | INET_N_1649   |      0
 Zeebrugge                  | INET_N_1834   |      0
 Porto Levante LNG Terminal |               |      0
(30 rows)
```

So all terminals are connected to a generic node, with a distance of 0 (exact match), this is a good sign. But now only the lng terminals are connected to the generic_nodes, but not to the shipping routes. 



First we check how far each lng terminal is from a nodes we can find
``` sql 

SELECT
  t.name                                        AS terminal,
  v.id                                          AS maritime_vertex_id,
  ROUND(ST_Distance(
    ST_Transform(t.geom, 3857),
    ST_Transform(v.geom, 3857)
  ))                                            AS dist_to_shipping_m
FROM lng_terminals t
CROSS JOIN LATERAL (
  SELECT id, geom
  FROM   maritime_routes_vertices
  ORDER BY t.geom <-> geom
  LIMIT  1
) v
ORDER BY dist_to_shipping_m;

-- output
terminal          | maritime_vertex_id | dist_to_shipping_m 
----------------------------+--------------------+--------------------
 Huelva                     |               3898 |               1411
 Dragon                     |               4410 |               1443
 Toscana                    |               7782 |               2783
 Porto Levante LNG Terminal |               8380 |               4647
 Panigaglia                 |               7631 |               5278
 Sagunto                    |               5371 |               5885
 Isle Of Grain              |               5541 |               5932
 Bilbao                     |               4830 |               6006
 Klaipeda                   |              10679 |               6147
 Montoir De Bretagne        |               5027 |               7557
 Fos Cavaou                 |               6373 |               7717
 Pori                       |              10755 |               7930
 El Musel                   |               4236 |               8739
 South Hook                 |               4410 |               9026
 Cartagena                  |               5257 |              10065
 Gate Rotterdam             |               6144 |              11041
 Dunkerque                  |               5801 |              11358
 Delimara                   |               8994 |              12169
 Swinoujscie                |               8903 |              12946
 Revithoussa                |              11045 |              13317
 Sines                      |               3629 |              13663
 Fos Tonkin                 |               6373 |              14185
 Gothenburg                 |               8265 |              15431
 Zeebrugge                  |               5970 |              15516
 Riga                       |              11243 |              15950
 Mugardos                   |               3715 |              18361
 Barcelona                  |               5802 |              19649
 Teesside                   |               5244 |              20728
 Cavarzere                  |               8369 |              31402
 Tallinn                    |              11437 |              38311
```


so the maritime_routes dont perfectly match the lng terminals, the best results are obtained with higher resolution data (marnet_plus_5km.gpkg) but this overloads the map. Later we can add different resolutions on zoom in, but for now this is fine. 


``` sql 
-- update the shipping side of terminal_connections
UPDATE terminal_connections tc
SET
  shipping_node_id    = snap.maritime_vertex_id,
  dist_to_shipping_m  = snap.dist_m,
  connector_shipping  = ST_MakeLine(t.geom, v.geom)
FROM (
  SELECT
    t.id                                      AS terminal_id,
    v.id                                      AS maritime_vertex_id,
    ST_Distance(
      ST_Transform(t.geom, 3857),
      ST_Transform(v.geom, 3857)
    )                                         AS dist_m,
    v.geom                                    AS vertex_geom
  FROM lng_terminals t
  CROSS JOIN LATERAL (
    SELECT id, geom
    FROM   maritime_routes_vertices
    ORDER BY t.geom <-> geom
    LIMIT  1
  ) v
) snap
JOIN lng_terminals t ON t.id = snap.terminal_id
JOIN maritime_routes_vertices v ON v.id = snap.maritime_vertex_id
WHERE tc.terminal_id = snap.terminal_id;
```



``` sql 
CREATE VIEW unified_network AS

  SELECT
    id,
    from_node_id                          AS source,
    to_node_id                            AS target,
    length_km                             AS cost,
    'pipeline'                            AS network
  FROM pipeline_segments

  UNION ALL

  SELECT
    id + 1000000,
    source + 10000000                     AS source,
    target + 10000000                     AS target,
    ST_Length(geometry::geography) / 1000.0   AS cost,   -- metres → km
    'maritime'                            AS network
  FROM maritime_routes

  UNION ALL

  SELECT
    id + 2000000,
    pipeline_node_id                      AS source,
    shipping_node_id + 10000000           AS target,
    (dist_to_pipeline_m + dist_to_shipping_m) / 1000.0  AS cost,  -- metres → km
    'terminal_bridge'                     AS network
  FROM terminal_connections
  WHERE pipeline_node_id IS NOT NULL AND shipping_node_id IS NOT NULL

  UNION ALL

  SELECT
    id + 3000000,
    shipping_node_id + 10000000           AS source,
    pipeline_node_id                      AS target,
    (dist_to_pipeline_m + dist_to_shipping_m) / 1000.0  AS cost,
    'terminal_bridge_rev'                 AS network
  FROM terminal_connections
  WHERE pipeline_node_id IS NOT NULL AND shipping_node_id IS NOT NULL;
```






Now theres a single pipeline_segment without any from or to node id, this causes errors, therefore we delete it 
``` sql 
SELECT 
  id,
  from_node_id,
  to_node_id,
  length_km,
  ST_AsText(geom) AS geom_preview
FROM pipeline_segments
WHERE from_node_id IS NULL OR to_node_id IS NULL;
  id  | from_node_id | to_node_id | length_km |                   geom_preview                    
------+--------------+------------+-----------+---------------------------------------------------
 5242 |              |            |      9.52 | LINESTRING(17.14068 48.91482,17.028471 48.871374)
(1 row)
```


``` sql 
DELETE FROM pipeline_segments WHERE id = 5242;
``` 



now we can query distances 
``` sql 
SELECT
  r.seq,
  r.node,
  r.edge,
  r.cost                              AS segment_km,
  sum(r.cost) OVER (ORDER BY r.seq)  AS cumulative_km,
  u.network
FROM pgr_dijkstra(
  'SELECT id, source, target, cost FROM unified_network',
  142,
  5901 + 10000000,
  directed := false
) AS r
JOIN unified_network u ON u.id = r.edge
ORDER BY r.seq;
```







``` sql 
ALTER TABLE lng_terminals
  ADD COLUMN processing_cost float DEFAULT 0,  -- cost per unit (€/MWh, $/mmBtu, whatever unit fits)
  ADD COLUMN capacity_tpa    float,             -- optional: max throughput constraint
  ADD COLUMN operator        text;              -- optional: useful for filtering
```