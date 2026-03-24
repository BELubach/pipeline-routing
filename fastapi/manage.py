#!/usr/bin/env python3
"""
Management CLI for FastAPI application
Usage: python manage.py <command> [options]
"""

import argparse
import sys
from pathlib import Path

# Add app to path
sys.path.insert(0, str(Path(__file__).parent))


def import_pipelines(args):
    """Import GEM pipeline data into the database"""
    from boot.db_setup.import_gem_pipelines import main as import_main, import_geojson, import_known_nodes
    import psycopg2
    from app.core.config import settings
    
    # Build DSN from settings
    dsn = (
        f"postgresql://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}"
        f"@{settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}"
    )
    
    print(f"Connecting to database: {settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}")
    conn = psycopg2.connect(dsn)
    
    print("\n--- Seeding known nodes (hubs, LNG terminals, etc.) ---")
    import_known_nodes(conn)
    
    if not args.seed_nodes_only:
        if not Path(args.geojson).exists():
            print(f"\nGeoJSON not found at {args.geojson}")
            print("Download from: https://globalenergymonitor.org/projects/global-gas-infrastructure-tracker/")
            print("Or: https://geoplatform.tools4msp.eu/layers/geonode:Gas_pipelines")
            print("\nRunning with seed nodes only.")
        else:
            print("\n--- Importing GeoJSON pipeline segments ---")
            import_geojson(conn, args.geojson, europe_only=not args.global_scope)
    
    conn.close()
    print("\n✅ Pipeline import completed successfully!")


def create_admin(args):
    """Create a superuser account"""
    import asyncio
    from app.db.session import AsyncSessionLocal
    from app.crud.crud_user import user as crud_user
    from app.schemas.user import UserCreate
    from app.core.security import get_password_hash
    
    async def _create():
        async with AsyncSessionLocal() as session:
            # Check if user exists
            existing = await crud_user.get_by_email(session, email=args.email)
            if existing:
                print(f"❌ User with email {args.email} already exists!")
                return
            
            # Create user
            user_in = UserCreate(
                email=args.email,
                password=args.password,
                full_name=args.name or "Admin User",
                role="admin"
            )
            user = await crud_user.create(session, obj_in=user_in)
            await session.commit()
            print(f"✅ Admin user created successfully!")
            print(f"   Email: {user.email}")
            print(f"   Role: {user.role}")
    
    asyncio.run(_create())


def init_db(args):
    """Initialize database with default data"""
    import asyncio
    from app.db.init_db import init_db as _init_db
    from app.db.session import AsyncSessionLocal
    
    async def _init():
        async with AsyncSessionLocal() as session:
            await _init_db(session)
            print("✅ Database initialized successfully!")
    
    asyncio.run(_init())


def db_shell(args):
    """Open a database shell (psql)"""
    import subprocess
    from app.core.config import settings
    
    env = {
        'PGPASSWORD': settings.POSTGRES_PASSWORD,
    }
    
    cmd = [
        'psql',
        '-h', settings.POSTGRES_HOST,
        '-p', settings.POSTGRES_PORT,
        '-U', settings.POSTGRES_USER,
        '-d', settings.POSTGRES_DB,
    ]
    
    try:
        subprocess.run(cmd, env=env, check=True)
    except FileNotFoundError:
        print("❌ psql command not found. Please install PostgreSQL client tools.")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error connecting to database: {e}")


def run_sql(args):
    """Execute SQL file against the database"""
    import psycopg2
    from app.core.config import settings
    
    sql_file = Path(args.file)
    if not sql_file.exists():
        print(f"❌ SQL file not found: {sql_file}")
        return
    
    dsn = (
        f"postgresql://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}"
        f"@{settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}"
    )
    
    print(f"Executing SQL from: {sql_file}")
    conn = psycopg2.connect(dsn)
    conn.autocommit = True
    cursor = conn.cursor()
    
    with open(sql_file, 'r', encoding='utf-8') as f:
        sql = f.read()
        try:
            # Execute the entire file at once (handles multi-statement SQL and functions)
            cursor.execute(sql)
            print("✅ SQL executed successfully!")
        except Exception as e:
            print(f"❌ Error executing SQL: {e}")
        finally:
            cursor.close()
            conn.close()


def main():
    parser = argparse.ArgumentParser(
        description='FastAPI Management CLI',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    subparsers = parser.add_subparsers(title='commands', dest='command', help='Available commands')
    
    # import-pipelines command
    import_parser = subparsers.add_parser('import-pipelines', help='Import GEM pipeline data')
    import_parser.add_argument(
        '--geojson',
        default='./data/GEM-GGIT-Gas-Pipelines-2025-11.geojson',
        help='Path to GEM pipeline GeoJSON file (default: ./data/GEM-GGIT-Gas-Pipelines-2025-11.geojson)'
    )

    import_parser.add_argument(
        '--global-scope',
        action='store_true',
        help='Import global pipelines (default: Europe only)'
    )
    import_parser.set_defaults(func=import_pipelines)
    
    # create-admin command
    admin_parser = subparsers.add_parser('create-admin', help='Create a superuser account')
    admin_parser.add_argument('--email', required=True, help='Admin email address')
    admin_parser.add_argument('--password', required=True, help='Admin password')
    admin_parser.add_argument('--name', help='Full name (optional)')
    admin_parser.set_defaults(func=create_admin)
    
    # init-db command
    init_parser = subparsers.add_parser('init-db', help='Initialize database with default data')
    init_parser.set_defaults(func=init_db)
    
    # db-shell command
    shell_parser = subparsers.add_parser('db-shell', help='Open a database shell (psql)')
    shell_parser.set_defaults(func=db_shell)
    
    # run-sql command
    sql_parser = subparsers.add_parser('run-sql', help='Execute SQL file against the database')
    sql_parser.add_argument('file', help='Path to SQL file')
    sql_parser.set_defaults(func=run_sql)
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Execute the command
    args.func(args)


if __name__ == '__main__':
    main()
