"""
Integration tests for plant endpoints

Plant model requires PostGIS geometry columns which SQLite doesn't support,
so we mock only the CRUD layer while testing real endpoint logic and auth.
"""
import pytest
from unittest.mock import patch, MagicMock
from httpx import AsyncClient
from datetime import datetime


@pytest.fixture(autouse=True)
def mock_geometry_conversion():
    """Mock geometry conversion functions for all plant tests"""
    with patch("app.api.v1.endpoints.plants.to_shape") as mock_to_shape, \
         patch("app.api.v1.endpoints.plants.mapping") as mock_mapping:
        
        # Mock to_shape to return a mock geometry object
        mock_geom = MagicMock()
        mock_geom.geom_type = "Polygon"
        mock_geom.exterior.coords = [[4.89, 52.37], [4.90, 52.37], [4.90, 52.38], [4.89, 52.38], [4.89, 52.37]]
        mock_to_shape.return_value = mock_geom
        
        # Mock mapping to return GeoJSON dict
        mock_mapping.return_value = {
            "type": "Polygon",
            "coordinates": [[[4.89, 52.37], [4.90, 52.37], [4.90, 52.38], [4.89, 52.38], [4.89, 52.37]]]
        }
        
        yield {"to_shape": mock_to_shape, "mapping": mock_mapping}


@pytest.mark.integration
class TestCreatePlantEndpoint:
    """Test the POST /api/v1/plants endpoint"""
    
    @patch("app.api.v1.endpoints.plants.crud_plant.create_plant")
    async def test_create_plant(
        self,
        mock_create,
        client: AsyncClient,
        auth_headers: dict
    ):
        """Test creating a new plant"""
        # Mock the CRUD response
        mock_plant = MagicMock()
        mock_plant.id = 1
        mock_plant.name = "Test Power Plant"
        mock_plant.created_at = datetime.now()
        mock_plant.geometry = "mocked_geometry"  # Will be converted by mocked to_shape/mapping
        mock_create.return_value = mock_plant
        
        plant_data = {
            "name": "Test Power Plant",
            "geometry": {
                "type": "Polygon",
                "coordinates": [
                    [
                        [4.89, 52.37],
                        [4.90, 52.37],
                        [4.90, 52.38],
                        [4.89, 52.38],
                        [4.89, 52.37]
                    ]
                ]
            }
        }
        
        response = await client.post(
            "/api/v1/plants",
            json=plant_data,
            headers=auth_headers
        )
        
        assert response.status_code == 201
        data = response.json()
        
        assert data["name"] == "Test Power Plant"
        assert "id" in data
        mock_create.assert_called_once()
    
    async def test_create_plant_unauthorized(
        self,
        client: AsyncClient
    ):
        """Test that creating plant without auth fails"""
        plant_data = {
            "name": "Unauthorized Plant",
            "geometry": {
                "type": "Polygon",
                "coordinates": [[[4.89, 52.37], [4.90, 52.37], [4.90, 52.38], [4.89, 52.37]]]
            }
        }
        
        response = await client.post(
            "/api/v1/plants",
            json=plant_data
        )
        
        assert response.status_code == 401
    
    async def test_create_plant_invalid_geometry_type(
        self,
        client: AsyncClient,
        auth_headers: dict
    ):
        """Test that creating plant with non-Polygon geometry fails"""
        plant_data = {
            "name": "Invalid Geometry Plant",
            "geometry": {
                "type": "Point",  # Should be Polygon
                "coordinates": [4.89, 52.37]
            }
        }
        
        response = await client.post(
            "/api/v1/plants",
            json=plant_data,
            headers=auth_headers
        )
        
        assert response.status_code == 422
    
    async def test_create_plant_missing_fields(
        self,
        client: AsyncClient,
        auth_headers: dict
    ):
        """Test validation for missing required fields"""
        response = await client.post(
            "/api/v1/plants",
            json={"name": "Incomplete Plant"},
            headers=auth_headers
        )
        
        assert response.status_code == 422


@pytest.mark.integration
class TestListPlantsEndpoint:
    """Test the GET /api/v1/plants endpoint"""
    
    @patch("app.api.v1.endpoints.plants.crud_plant.get_plants")
    async def test_list_plants(
        self,
        mock_get_plants,
        client: AsyncClient,
        auth_headers: dict
    ):
        """Test listing all plants"""
        # Mock plant list
        mock_plant1 = MagicMock()
        mock_plant1.id = 1
        mock_plant1.name = "Plant 1"
        mock_plant1.geometry = "mock_geometry_1"
        mock_plant1.created_at = datetime.now()
        
        mock_plant2 = MagicMock()
        mock_plant2.id = 2
        mock_plant2.name = "Plant 2"
        mock_plant2.geometry = "mock_geometry_2"
        mock_plant2.created_at = datetime.now()
        
        mock_get_plants.return_value = [mock_plant1, mock_plant2]
        
        # List plants
        response = await client.get(
            "/api/v1/plants",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert len(data) == 2
        assert any(p["name"] == "Plant 1" for p in data)
        assert any(p["name"] == "Plant 2" for p in data)
        mock_get_plants.assert_called_once()
    
    @patch("app.api.v1.endpoints.plants.crud_plant.get_plants")
    async def test_list_plants_pagination(
        self,
        mock_get_plants,
        client: AsyncClient,
        auth_headers: dict
    ):
        """Test pagination parameters"""
        # Mock paginated result
        mock_plants = []
        for i in range(2):
            mock_plant = MagicMock()
            mock_plant.id = i + 3  # Skip IDs 1-2
            mock_plant.name = f"Plant {i}"
            mock_plant.geometry = f"mock_geometry_{i}"
            mock_plant.created_at = datetime.now()
            mock_plants.append(mock_plant)
        
        mock_get_plants.return_value = mock_plants
        
        # Test skip parameter
        response = await client.get(
            "/api/v1/plants?skip=2&limit=2",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert len(data) == 2
        # Verify CRUD was called (arguments are db, skip=2, limit=2)
        mock_get_plants.assert_called_once()
    
    async def test_list_plants_unauthorized(
        self,
        client: AsyncClient
    ):
        """Test that listing plants without auth fails"""
        response = await client.get("/api/v1/plants")
        
        assert response.status_code == 401


@pytest.mark.integration
class TestGetPlantEndpoint:
    """Test the GET /api/v1/plants/{plant_id} endpoint"""
    
    @patch("app.api.v1.endpoints.plants.crud_plant.get_plant_by_id")
    async def test_get_plant(
        self,
        mock_get_plant,
        client: AsyncClient,
        auth_headers: dict
    ):
        """Test getting a specific plant by ID"""
        # Mock plant
        mock_plant = MagicMock()
        mock_plant.id = 1
        mock_plant.name = "Specific Plant"
        mock_plant.geometry = "mock_geometry"
        mock_plant.created_at = datetime.now()
        mock_get_plant.return_value = mock_plant
        
        # Get the plant
        response = await client.get(
            "/api/v1/plants/1",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["id"] == 1
        assert data["name"] == "Specific Plant"
        # Verify CRUD was called
        mock_get_plant.assert_called_once()
    
    @patch("app.api.v1.endpoints.plants.crud_plant.get_plant_by_id")
    async def test_get_plant_not_found(
        self,
        mock_get_plant,
        client: AsyncClient,
        auth_headers: dict
    ):
        """Test getting non-existent plant"""
        mock_get_plant.return_value = None
        
        response = await client.get(
            "/api/v1/plants/99999",
            headers=auth_headers
        )
        
        assert response.status_code == 404
    
    async def test_get_plant_unauthorized(
        self,
        client: AsyncClient
    ):
        """Test that getting plant without auth fails"""
        response = await client.get("/api/v1/plants/1")
        
        assert response.status_code == 401


@pytest.mark.integration
class TestUpdatePlantEndpoint:
    """Test the PUT /api/v1/plants/{plant_id} endpoint"""
    
    @patch("app.api.v1.endpoints.plants.crud_plant.update_plant")
    async def test_update_plant_name(
        self,
        mock_update,
        client: AsyncClient,
        auth_headers: dict
    ):
        """Test updating plant name"""
        # Mock updated plant
        mock_plant = MagicMock()
        mock_plant.id = 1
        mock_plant.name = "Updated Name"
        mock_plant.geometry = "mock_geometry"
        mock_plant.created_at = datetime.now()
        mock_plant.updated_at = datetime.now()
        mock_update.return_value = mock_plant
        
        # Update the plant
        response = await client.put(
            "/api/v1/plants/1",
            json={"name": "Updated Name"},
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["name"] == "Updated Name"
        assert data["id"] == 1
        mock_update.assert_called_once()
    
    @patch("app.api.v1.endpoints.plants.crud_plant.update_plant")
    async def test_update_plant_geometry(
        self,
        mock_update,
        client: AsyncClient,
        auth_headers: dict
    ):
        """Test updating plant geometry"""
        # Mock updated plant
        mock_plant = MagicMock()
        mock_plant.id = 1
        mock_plant.name = "Geometry Test"
        mock_plant.geometry = "mock_updated_geometry"
        mock_plant.created_at = datetime.now()
        mock_plant.updated_at = datetime.now()
        mock_update.return_value = mock_plant
        
        # Update geometry
        new_geometry = {
            "type": "Polygon",
            "coordinates": [
                [
                    [5.0, 52.0],
                    [5.1, 52.0],
                    [5.1, 52.1],
                    [5.0, 52.1],
                    [5.0, 52.0]
                ]
            ]
        }
        
        response = await client.put(
            "/api/v1/plants/1",
            json={"geometry": new_geometry},
            headers=auth_headers
        )
        
        assert response.status_code == 200
        mock_update.assert_called_once()
    
    @patch("app.api.v1.endpoints.plants.crud_plant.update_plant")
    async def test_update_plant_not_found(
        self,
        mock_update,
        client: AsyncClient,
        auth_headers: dict
    ):
        """Test updating non-existent plant"""
        mock_update.return_value = None
        
        response = await client.put(
            "/api/v1/plants/99999",
            json={"name": "New Name"},
            headers=auth_headers
        )
        
        assert response.status_code == 404
    
    async def test_update_plant_unauthorized(
        self,
        client: AsyncClient
    ):
        """Test that updating plant without auth fails"""
        response = await client.put(
            "/api/v1/plants/1",
            json={"name": "Updated"}
        )
        
        assert response.status_code == 401


@pytest.mark.integration
class TestDeletePlantEndpoint:
    """Test the DELETE /api/v1/plants/{plant_id} endpoint"""
    
    @patch("app.api.v1.endpoints.plants.crud_plant.get_plant_by_id")
    @patch("app.api.v1.endpoints.plants.crud_plant.delete_plant")
    async def test_delete_plant(
        self,
        mock_delete,
        mock_get,
        client: AsyncClient,
        auth_headers: dict
    ):
        """Test deleting a plant"""
        # First call returns plant exists, second call (after delete) returns None
        mock_get.side_effect = [
            MagicMock(id=1, name="To Delete"),  # Plant exists before delete
            None  # Plant not found after delete
        ]
        mock_delete.return_value = True
        
        # Delete the plant
        response = await client.delete(
            "/api/v1/plants/1",
            headers=auth_headers
        )
        
        assert response.status_code == 204
        mock_delete.assert_called_once()
    
    @patch("app.api.v1.endpoints.plants.crud_plant.delete_plant")
    async def test_delete_plant_not_found(
        self,
        mock_delete,
        client: AsyncClient,
        auth_headers: dict
    ):
        """Test deleting non-existent plant"""
        mock_delete.return_value = False
        
        response = await client.delete(
            "/api/v1/plants/99999",
            headers=auth_headers
        )
        
        assert response.status_code == 404
    
    async def test_delete_plant_unauthorized(
        self,
        client: AsyncClient
    ):
        """Test that deleting plant without auth fails"""
        response = await client.delete("/api/v1/plants/1")
        
        assert response.status_code == 401


@pytest.mark.integration
class TestPlantCRUDWorkflow:
    """Integration test for complete CRUD workflow"""
    
    @patch("app.api.v1.endpoints.plants.crud_plant.create_plant")
    @patch("app.api.v1.endpoints.plants.crud_plant.get_plant_by_id")
    @patch("app.api.v1.endpoints.plants.crud_plant.update_plant")
    @patch("app.api.v1.endpoints.plants.crud_plant.delete_plant")
    async def test_complete_plant_workflow(
        self,
        mock_delete,
        mock_update,
        mock_get,
        mock_create,
        client: AsyncClient,
        auth_headers: dict
    ):
        """Test create -> read -> update -> delete workflow"""
        # Setup mocks
        mock_plant = MagicMock()
        mock_plant.id = 1
        mock_plant.name = "Workflow Plant"
        mock_plant.geometry = "mock_geometry"
        mock_plant.created_at = datetime.now()
        mock_create.return_value = mock_plant
        
        # 1. Create
        plant_data = {
            "name": "Workflow Plant",
            "geometry": {
                "type": "Polygon",
                "coordinates": [
                    [
                        [4.89, 52.37],
                        [4.90, 52.37],
                        [4.90, 52.38],
                        [4.89, 52.38],
                        [4.89, 52.37]
                    ]
                ]
            }
        }
        
        create_response = await client.post(
            "/api/v1/plants",
            json=plant_data,
            headers=auth_headers
        )
        assert create_response.status_code == 201
        plant = create_response.json()
        plant_id = plant["id"]
        
        # 2. Read
        mock_get.return_value = mock_plant
        get_response = await client.get(
            f"/api/v1/plants/{plant_id}",
            headers=auth_headers
        )
        assert get_response.status_code == 200
        assert get_response.json()["name"] == "Workflow Plant"
        
        # 3. Update
        mock_updated_plant = MagicMock()
        mock_updated_plant.id = plant_id
        mock_updated_plant.name = "Updated Workflow Plant"
        mock_updated_plant.geometry = "mock_geometry"
        mock_updated_plant.created_at = mock_plant.created_at
        mock_updated_plant.updated_at = datetime.now()
        mock_update.return_value = mock_updated_plant
        
        update_response = await client.put(
            f"/api/v1/plants/{plant_id}",
            json={"name": "Updated Workflow Plant"},
            headers=auth_headers
        )
        assert update_response.status_code == 200
        assert update_response.json()["name"] == "Updated Workflow Plant"
        
        # 4. Delete
        mock_delete.return_value = True
        delete_response = await client.delete(
            f"/api/v1/plants/{plant_id}",
            headers=auth_headers
        )
        assert delete_response.status_code == 204
        
        # 5. Verify deletion
        mock_get.return_value = None
        get_deleted_response = await client.get(
            f"/api/v1/plants/{plant_id}",
            headers=auth_headers
        )
        assert get_deleted_response.status_code == 404
