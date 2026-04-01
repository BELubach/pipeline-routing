# FastAPI Application with SQLAlchemy, Alembic, and PostGIS

A production-ready FastAPI application with user authentication (JWT), PostgreSQL database with PostGIS support, and Alembic migrations.

## ⚡ Quick Start (with Docker)

```bash
# 1. Clone and navigate to project
cd fastapi

# 2. Create virtual environment and install dependencies
python -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Linux/Mac
pip install -r requirements.txt

# 3. Copy environment file and update SECRET_KEY
copy .env.example .env  # Windows
# cp .env.example .env  # Linux/Mac

# 4. Start PostgreSQL with PostGIS
docker-compose up -d

# 5. Run database migrations
alembic revision --autogenerate -m "Initial migration"
alembic upgrade head

# 6. Start the application
uvicorn app.main:app --reload

# 7. Open your browser
# API Docs: http://localhost:8000/api/v1/docs
```

## Project Structure

```
fastapi/
├── app/
│   ├── api/
│   │   └── v1/
│   │       ├── endpoints/
│   │       │   ├── auth.py          # Authentication endpoints
│   │       │   └── users.py         # User management endpoints
│   │       └── api.py               # API router aggregation
│   ├── core/
│   │   ├── config.py                # Application configuration
│   │   └── security.py              # Security utilities (JWT, hashing)
│   ├── crud/
│   │   └── crud_user.py             # User CRUD operations
│   ├── db/
│   │   ├── base.py                  # Import all models for Alembic
│   │   ├── init_db.py               # Database initialization
│   │   └── session.py               # Database session management
│   ├── models/
│   │   └── user.py                  # User database model
│   ├── schemas/
│   │   ├── token.py                 # Token schemas
│   │   └── user.py                  # User Pydantic schemas
│   └── main.py                      # FastAPI application entry point
├── alembic/
│   ├── versions/                    # Migration files
│   ├── env.py                       # Alembic environment configuration
│   └── script.py.mako              # Migration template
├── init-db/
│   └── 01-extensions.sql           # PostGIS initialization script
├── .env                             # Environment variables (create from .env.example)
├── .env.example                     # Example environment configuration
├── .gitignore                       # Git ignore patterns
├── alembic.ini                      # Alembic configuration
├── docker-compose.yml               # Docker services (PostgreSQL + PostGIS)
├── docker-compose.override.yml.example  # Docker override example
├── Makefile                         # Helper commands (Linux/Mac)
├── make.bat                         # Helper commands (Windows)
├── requirements.txt                 # Python dependencies
└── README.md                        # This file
```

## 📋 Prerequisites

- Python 3.10+
- Docker & Docker Compose (recommended) **OR** PostgreSQL 14+ with PostGIS
- pip and virtualenv

## 🚀 Installation & Setup

### 1. Clone the Repository

```bash
git clone <your-repository-url>
cd fastapi
```

### 2. Create Virtual Environment

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# Linux/Mac
source .venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Set Up Environment Variables

Copy the example environment file and configure it:

```bash
# Windows
copy .env.example .env

# Linux/Mac
cp .env.example .env
```

Edit `.env` and update the following variables:

```env
# Generate a secure secret key (run: openssl rand -hex 32)
SECRET_KEY=secret-key-here

# Database credentials
POSTGRES_USER=your_db_user
POSTGRES_PASSWORD=your_db_password
POSTGRES_HOST=localhost
POSTGRES_PORT=5433
POSTGRES_DB=your_database_name
```

### 5. Set Up PostgreSQL Database

```bash
# Start PostgreSQL with PostGIS
docker-compose up -d

# Check if the database is running
docker-compose ps

# View logs
docker-compose logs -f postgres

# Stop the database
docker-compose down

# Stop and remove all data (caution: destroys all data)
docker-compose down -v
```

**Optional: PgAdmin**

The Docker Compose file includes PgAdmin for database management. To start it:

```bash
# Start PostgreSQL with PgAdmin
docker-compose --profile tools up -d

# Access PgAdmin at: http://localhost:5050
# Email: admin@admin.com
# Password: admin
```

To connect to the database in PgAdmin:
- Host: postgres (or localhost if connecting from outside Docker)
- Port: 5433 (Docker host port, or 5432 if inside Docker network)
- Database: fastapi_db (or your POSTGRES_DB)
- Username: postgres (or your POSTGRES_USER)
- Password: postgres (or your POSTGRES_PASSWORD)

**Note:** The Docker PostgreSQL uses port **5433** on your host machine to avoid conflicts with any local PostgreSQL installation on port 5432.

```
uvicorn app.main:app --reload
```

## Database Migrations with Alembic

### Running Initial Migration

After setting up your database and environment variables:

#### 1. Create Initial Migration

Generate the first migration based on your models:

```bash
alembic revision --autogenerate -m "Initial migration with user model"
```

This will create a new migration file in `alembic/versions/` directory.

#### 2. Apply Migration to Database

Run the migration to create tables in your database:

```bash
alembic upgrade head
```

### Common Alembic Commands

```bash
# Show current database version
alembic current

# Show migration history
alembic history

# Upgrade to specific version
alembic upgrade <revision_id>

# Downgrade one version
alembic downgrade -1

# Downgrade to specific version
alembic downgrade <revision_id>

# Downgrade all migrations (back to empty database)
alembic downgrade base

# Create empty migration (manual changes)
alembic revision -m "Description of changes"

# Generate SQL without applying (dry run)
alembic upgrade head --sql
```


### Set Up Database Functions

After the migration, run the SQL script to create functions and views:

```bash
python manage.py run-sql boot/pipeline_functions.sql
```

**See [boot/README.md](boot/README.md) for detailed initialization guide.**

This creates:
- `recompute_edge_costs()` - Function to compute routing costs
- `nearest_node()` - Find nearest pipeline node to coordinates
- `find_cheapest_gas_route()` - pgRouting pathfinding wrapper
- `route_by_coordinates()` - High-level routing function
- `pipeline_routing_graph` - View for pgRouting
- Tariff rules seed data

### 5Import Pipeline Data

#### Seed Known Nodes Only (Quick Start)

```bash
python manage.py import-pipelines
```

This imports ~50 well-known hubs, LNG terminals, and border crossings.



then go to https://globalenergymonitor.org/projects/global-gas-infrastructure-tracker/
and download the geojson data and put it in the ./data folder
```

python manage.py import-pipelines --geojson ./data/GEM-GGIT-Gas-Pipelines-2025-11.geojson
```


## Running the Application

### Development Mode

Run the application with auto-reload enabled:

```bash
# Using uvicorn directly
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Or using Python
python -m app.main
```

The API will be available at:
- **API**: http://localhost:8000
- **Interactive Docs (Swagger)**: http://localhost:8000/api/v1/docs
- **Alternative Docs (ReDoc)**: http://localhost:8000/api/v1/redoc

### Production Mode

For production, use a production-grade ASGI server:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

## API Endpoints

### Authentication

#### User Roles

The application supports three user roles that are baked into JWT tokens:

- **CLUSTER_ADMIN** - Full administrative access to the cluster
- **COMPANY_OWNER** - Company-level access and management
- **UTILITY_PROVIDER** - Utility provider access and operations

Roles are included in both access and refresh tokens and can be used for authorization checks.

#### Register a New User
```http
POST /api/v1/auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "securepassword123",
  "role": "COMPANY_OWNER",
  "is_active": true,
  "is_superuser": false
}
```

**Available roles:** `CLUSTER_ADMIN`, `COMPANY_OWNER`, `UTILITY_PROVIDER`  
**Default role:** `COMPANY_OWNER`

#### Login (Simple JSON REST API)
```http
POST /api/v1/auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "securepassword123"
}
```

Response:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

#### Login (OAuth2 Form - for OpenAPI Schema)
```http
POST /api/v1/auth/login/oauth2
Content-Type: application/x-www-form-urlencoded

username=user@example.com&password=securepassword123
```

Response (same as above with access and refresh tokens).

#### Refresh Access Token
```http
POST /api/v1/auth/refresh
Content-Type: application/json

{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

Response:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

#### Get Current User Profile
```http
GET /api/v1/auth/me
Authorization: Bearer <your_access_token>
```


## Helper Scripts

For convenience, helper scripts are provided for common tasks:

### Windows (`make.bat`)

```bash
# Show available commands
make.bat help

# Start database
make.bat db-up

# Run migrations
make.bat migrate

# Create new migration
make.bat migrate-create "Add new field"

# Run application
make.bat run

# Stop database
make.bat db-down

# Show database logs
make.bat db-logs

# Clean cache files
make.bat clean
```

### Linux/Mac (`Makefile`)

```bash
# Show available commands
make help

# Start database
make db-up

# Run migrations
make migrate

# Create new migration
make migrate-create MSG="Add new field"

# Run application
make run

# Stop database
make db-down

# Show database logs
make db-logs

# Clean cache files
make clean
```

### Using PostGIS Features

To use PostGIS geometry types in your models:

```python
from geoalchemy2 import Geometry
from sqlalchemy import Column, Integer, String

class Location(Base):
    __tablename__ = "locations"
    
    id = Column(Integer, primary_key=True)
    name = Column(String)
    point = Column(Geometry('POINT', srid=4326))
    polygon = Column(Geometry('POLYGON', srid=4326))
```

### Using Role-Based Permissions

The application includes role-based access control baked into JWT tokens. Use the permission helpers to protect endpoints:

```python
from fastapi import APIRouter, Depends
from app.core.permissions import require_role, RequireClusterAdmin
from app.schemas.user import User, UserRole

router = APIRouter()

# Method 1: Using the factory function
@router.get("/admin-only")
async def admin_endpoint(
    current_user: User = Depends(require_role([UserRole.CLUSTER_ADMIN]))
):
    return {"message": "Admin access granted"}

# Method 2: Using pre-defined dependencies
@router.get("/cluster-ops")
async def cluster_ops(
    current_user: User = RequireClusterAdmin
):
    return {"message": "Managing cluster", "user_role": current_user.role}

# Method 3: Multiple roles allowed
@router.get("/owner-or-admin")
async def owner_or_admin(
    current_user: User = Depends(require_role([
        UserRole.CLUSTER_ADMIN, 
        UserRole.COMPANY_OWNER
    ]))
):
    return {"message": "Owner or admin access"}
```

## Environment Variables Reference

| Variable | Description | Default |
|----------|-------------|---------|
| `PROJECT_NAME` | Application name | FastAPI App |
| `VERSION` | API version | 1.0.0 |
| `SECRET_KEY` | JWT secret key | **Required** |
| `ALGORITHM` | JWT algorithm | HS256 |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Access token expiration | 30 |
| `REFRESH_TOKEN_EXPIRE_MINUTES` | Refresh token expiration | 43200 (30 days) |
| `POSTGRES_USER` | Database user | **Required** |
| `POSTGRES_PASSWORD` | Database password | **Required** |
| `POSTGRES_HOST` | Database host | localhost |
| `POSTGRES_PORT` | Database port | 5433 |
| `POSTGRES_DB` | Database name | **Required** |

## Technology Stack

- **FastAPI** - Modern, fast web framework
- **SQLAlchemy 2.0** - ORM with async support
- **Alembic** - Database migration tool
- **PostgreSQL** - Relational database
- **PostGIS** - Spatial database extension
- **Pydantic** - Data validation
- **JWT** - Authentication tokens
- **Bcrypt** - Password hashing
- **Asyncpg** - Async PostgreSQL driver

