

import pytest
from httpx import AsyncClient

@pytest.mark.e2e
class TestGetAllSegmentsE2E:

    async def test_get_all_segments(
        self,
        client: AsyncClient
    ):
        """Test getting all shipping lanes"""
        response = await client.get(
            f"/api/v1/shipping-lanes"
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 239

        assert "id" in data[0]
        assert "from_node" in data[0]
        assert "to_node" in data[0]
        assert "distance_km" in data[0]
        assert "geometry" in data[0]

