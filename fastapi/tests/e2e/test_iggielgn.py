"""
Integration tests for authentication endpoints
"""
import asyncio
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.pipeline import NodesResponse


@pytest.mark.e2e
class TestIGGIELGNEndpoints:
    """Test the /api/v1/iggielgn endpoints"""
    
    async def test_get_generic_nodes(
        self,
        client: AsyncClient,
        db_session: AsyncSession
    ):
        """Test registering a new user"""
        response = await client.get(
            "/api/v1/iggielgn/nodes"
        )
        
        assert response.status_code == 200
        content = response.json()
        
        print("Response content:", content)  # Debug print
        assert content["metadata"] is not None
        assert content["data"] is not None

        assert content.metadata["record_count"] >= 0
        assert content.metadata["dataset_id"] == "iggielgn"


