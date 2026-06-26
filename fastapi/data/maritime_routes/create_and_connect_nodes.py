from sqlalchemy import create_engine, text

DATABASE_URL = "postgresql://postgres:postgres@localhost:5467/fastapi_db"

def extract_vertices(engine):
    with engine.connect() as conn:
        conn.execute(text("""
            INSERT INTO maritime_routes_vertices
            SELECT * FROM pgr_extractVertices(
                'SELECT id, geometry AS geom FROM maritime_routes'
            )
        """))
        conn.commit()
        print("✓ Vertices extracted")

def populate_source_target(engine):
    with engine.connect() as conn:
        conn.execute(text("""
            UPDATE maritime_routes AS e
            SET 
                source = v_start.id,
                target = v_end.id
            FROM 
                maritime_routes_vertices v_start,
                maritime_routes_vertices v_end
            WHERE 
                ST_DWithin(ST_StartPoint(e.geometry), v_start.geom, 0.00001)
                AND ST_DWithin(ST_EndPoint(e.geometry), v_end.geom, 0.00001)
        """))
        conn.commit()
        print("✓ Source/target populated")

def verify(engine):
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT id, source, target FROM maritime_routes LIMIT 5
        """))
        print("\nSample rows:")
        for row in result:
            print(f"  id={row.id}, source={row.source}, target={row.target}")

if __name__ == "__main__":
    engine = create_engine(DATABASE_URL)
    extract_vertices(engine)
    populate_source_target(engine)
    verify(engine)