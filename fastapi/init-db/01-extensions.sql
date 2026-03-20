-- Enable PostGIS extension
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS postgis_topology;

-- Optional: Enable additional PostGIS extensions
-- CREATE EXTENSION IF NOT EXISTS postgis_raster;
-- CREATE EXTENSION IF NOT EXISTS postgis_sfcgal;

-- Verify PostGIS installation
SELECT PostGIS_Version();
