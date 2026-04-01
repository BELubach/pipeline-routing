"""
Pytest configuration and fixtures for integration tests
"""
import asyncio
from typing import AsyncGenerator, Generator
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession


def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "e2e: end-to-end tests that require the Docker-backed database",
    )


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def auth_headers(client: AsyncClient, db_session: AsyncSession) -> dict:
    """Create authenticated user and return authorization headers"""
    from app.crud import crud_user
    from app.schemas.user import UserCreate
    
    # Try to get existing user first
    existing_user = await crud_user.get_user_by_email(db_session, email="test@example.com")
    
    if not existing_user:
        # Create test user
        user_in = UserCreate(
            email="test@example.com",
            password="testpass123",
            role="COMPANY_OWNER"
        )
        
        user = await crud_user.create_user(db_session, user_in=user_in)
        await db_session.commit()
    
    # Login to get token
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "test@example.com", "password": "testpass123"}
    )
    
    assert response.status_code == 200
    token_data = response.json()
    
    return {"Authorization": f"Bearer {token_data['access_token']}"}


@pytest.fixture
async def superuser_headers(client: AsyncClient, db_session: AsyncSession) -> dict:
    """Create superuser and return authorization headers"""
    from app.crud import crud_user
    from app.schemas.user import UserCreate
    
    # Try to get existing user first
    existing_user = await crud_user.get_user_by_email(db_session, email="admin@example.com")
    
    if not existing_user:
        # Create test superuser
        user_in = UserCreate(
            email="admin@example.com",
            password="adminpass123",
            role="CLUSTER_ADMIN",
            is_superuser=True
        )
        
        user = await crud_user.create_user(db_session, user_in=user_in)
        await db_session.commit()
    
    # Login to get token
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "admin@example.com", "password": "adminpass123"}
    )
    
    assert response.status_code == 200
    token_data = response.json()
    
    return {"Authorization": f"Bearer {token_data['access_token']}"}


# Mock data fixtures for pipeline tests
@pytest.fixture
def mock_route_response():
    """Mock response for route_by_coordinates function"""
    return [
        {
            "seq": 1,
            "node_id": 100,
            "node_name": "Node A",
            "edge_id": None,
            "segment_cost": 0.0,
            "cumulative_cost": 0.0,
            "segment_km": 0.0,
            "geometry": None,
            "snap_info": {
                "start_node_id": 100,
                "end_node_id": 200,
                "start_snap_km": 5.2,
                "end_snap_km": 3.8
            }
        },
        {
            "seq": 2,
            "node_id": 150,
            "node_name": "Node B",
            "edge_id": 1001,
            "segment_cost": 2.5,
            "cumulative_cost": 2.5,
            "segment_km": 50.0,
            "geometry": {
                "type": "LineString",
                "coordinates": [[4.9, 52.3], [5.0, 52.4]]
            },
            "snap_info": {
                "start_node_id": 100,
                "end_node_id": 200,
                "start_snap_km": 5.2,
                "end_snap_km": 3.8
            }
        },
        {
            "seq": 3,
            "node_id": 200,
            "node_name": "Node C",
            "edge_id": 1002,
            "segment_cost": 1.8,
            "cumulative_cost": 4.3,
            "segment_km": 35.0,
            "geometry": {
                "type": "LineString",
                "coordinates": [[5.0, 52.4], [5.2, 52.5]]
            },
            "snap_info": {
                "start_node_id": 100,
                "end_node_id": 200,
                "start_snap_km": 5.2,
                "end_snap_km": 3.8
            }
        }
    ]


@pytest.fixture
def mock_nearest_nodes():
    """Mock response for nearest_node function"""
    return [
        {
            "node_id": 100,
            "name": "TTF Hub",
            "node_type": "hub",
            "distance_km": 5.2
        },
        {
            "node_id": 101,
            "name": "Gate Terminal",
            "node_type": "lng_terminal",
            "distance_km": 12.7
        }
    ]


@pytest.fixture
def mock_pipeline_nodes():
    """Mock pipeline nodes data"""
    return [
        {
            "id": 100,
            "name": "TTF Hub",
            "node_type": "hub",
            "country": "NL",
            "is_trading_hub": True,
            "hub_code": "TTF",
            "lng_capacity_bcm": None,
            "lng_type": None,
            "lon": 4.89,
            "lat": 52.37
        },
        {
            "id": 101,
            "name": "Gate Terminal",
            "node_type": "lng_terminal",
            "country": "NL",
            "is_trading_hub": False,
            "hub_code": None,
            "lng_capacity_bcm": 12.0,
            "lng_type": "import",
            "lon": 4.01,
            "lat": 51.95
        }
    ]


@pytest.fixture
def mock_plant():
    """Mock plant object"""
    from unittest.mock import MagicMock
    from datetime import datetime
    
    plant = MagicMock()
    plant.id = 1
    plant.name = "Test Power Plant"
    plant.geometry = "SRID=4326;POLYGON((4.89 52.37, 4.90 52.37, 4.90 52.38, 4.89 52.38, 4.89 52.37))"
    plant.created_at = datetime.now()
    plant.updated_at = None
    
    return plant
