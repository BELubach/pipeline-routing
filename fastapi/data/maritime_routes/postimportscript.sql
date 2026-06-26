
-- old script that craetes a table of vertices from the maritime_routes table and populates the source and target columns in the maritime_routes table with the IDs of the start and end vertices.
-- replaced by alembic creating the schema and create_and_connect_nodes.py script that creates the vertices and populates the source and target columns in the maritime_routes table.


-- extract all unique start/end points from your edges and stores them as rows with assigned IDs.
CREATE TABLE maritime_routes_vertices AS
SELECT * FROM pgr_extractVertices('SELECT id, geometry AS geom FROM maritime_routes');


-- Adds a primary key and a spatial index so lookups against it are fast.
ALTER TABLE maritime_routes_vertices ADD PRIMARY KEY (id);
CREATE INDEX ON maritime_routes_vertices USING gist(geom);

-- Adds source and target columns to the maritime_routes table
ALTER TABLE maritime_routes ADD COLUMN IF NOT EXISTS source BIGINT;
ALTER TABLE maritime_routes ADD COLUMN IF NOT EXISTS target BIGINT;

-- Populates them with the IDs of the start and end vertices.
UPDATE maritime_routes AS e
SET 
  source = v_start.id,
  target = v_end.id
FROM 
  maritime_routes_vertices v_start,
  maritime_routes_vertices v_end
WHERE 
  ST_DWithin(ST_StartPoint(e.geometry), v_start.geom, 0.00001)
  AND ST_DWithin(ST_EndPoint(e.geometry), v_end.geom, 0.00001);



SELECT id, source, target FROM maritime_routes LIMIT 5;