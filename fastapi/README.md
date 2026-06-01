# FastAPI Application with SQLAlchemy, Alembic, and PostGIS

A production-ready FastAPI application with user authentication (JWT), PostgreSQL database with PostGIS support, and Alembic migrations.

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

## Prerequisites

- Python 3.14+
- Docker & Docker Compose (recommended) **OR** PostgreSQL 16+ with PostGIS
- pip and virtualenv


## Quick Start (with Docker)




### start docker database with PostGIS
```
docker-compose up -d

alembic upgrade head
``` 



### Run Fastapi app 
```bash
# Clone and navigate to project
cd fastapi

# Create virtual environment and install dependencies
python -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Linux/Mac
pip install -r requirements.txt

# Copy environment file and update SECRET_KEY
copy .env.example .env  # Windows
# cp .env.example .env  # Linux/Mac
uvicorn app.main:app --reload

# Open your browser
# API Docs: http://localhost:8000/api/v1/docs
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

