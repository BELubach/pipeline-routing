import geopandas as gpd
from sqlalchemy import create_engine



if __name__ == "__main__":
    engine = create_engine("postgresql://postgres:postgres@localhost:5467/fastapi_db")

    gdf = gpd.read_file("marnet_plus_20km.gpkg", layer="type")
    gdf.to_postgis(
        name="maritime_routes",
        con=engine,
        if_exists="append",
        index=False,
    )
