

import pytest
from httpx import AsyncClient

@pytest.mark.e2e
class TestGetShortestPathE2E:

    async def test_get_simple_route_from_two_ids(
        self,
        client: AsyncClient
    ):
        """Test getting a simple route between two nodes"""
        start_node_id = 32
        end_node_id = 55
        response = await client.get(
            f"/api/v1/routes/path/{start_node_id}/{end_node_id}"
        )

        assert response.status_code == 200
        data = response.json()

        assert isinstance(data, list)
        assert len(data) == 21 
        assert data[0]["start_node"] == start_node_id
        assert data[-1]["end_node"] == end_node_id
        assert data[-1]["total_distance"] == 1773.6
        


    async def test_get_simple_route_same_node(
        self,
        client: AsyncClient
    ):
        """Test getting a route from a node to itself raises an error"""
        node_id = 32
        response = await client.get(
            f"/api/v1/routes/path/{node_id}/{node_id}"
        )

        print("running some simple test ")
        print(response.json())
        assert response.status_code == 404
        assert response.json()["detail"] == 'No path found between nodes 32 and 32'



@pytest.mark.e2e
class TestGetNeighborsE2E:

    async def test_get_neighbors(
        self,
        client: AsyncClient
    ):
        """Test getting neighbors of a node"""
        node_id = 32
        response = await client.get(
            f"/api/v1/routes/neighbors/{node_id}"
        )

        assert response.status_code == 200
        data = response.json()

        assert isinstance(data, list)
        assert len(data) == 4 
        for neighbor in data:
            assert "neighbor_id" in neighbor
            assert "distance_km" in neighbor
            assert "segment_id" in neighbor
            assert neighbor["neighbor_id"] != node_id

    async def test_get_neighbors_nonexistent_node(
        self,
        client: AsyncClient
    ):
        """Test getting neighbors of a non-existent node returns empty list"""
        node_id = 9999 
        response = await client.get(
            f"/api/v1/routes/neighbors/{node_id}"
        )

        assert response.status_code == 404
        assert response.json()["detail"] == 'Node 9999 does not exist'


@pytest.mark.e2e
class TestGetRouteSummaryE2E:

    async def test_get_route_summary(
        self,
        client: AsyncClient
    ):
        """Test getting route summary between two nodes"""
        start_node_id = 32
        end_node_id = 55
        response = await client.get(
            f"/api/v1/routes/summary/{start_node_id}/{end_node_id}"
        )

        assert response.status_code == 200
        data = response.json()
        print(data)
        assert "start_node" in data
        assert "end_node" in data
        assert "total_distance" in data
        assert "segment_count" in data
        assert "node_count" in data
    

        assert data["start_node"] == start_node_id
        assert data["end_node"] == end_node_id
        assert data["total_distance"] == 1773.6
        assert data["segment_count"] == 20
        assert data['node_count'] == 21

    async def test_get_route_summary_nonexistent_nodes(
        self,
        client: AsyncClient
    ):
        """Test getting route summary with non-existent nodes returns error"""
        start_node_id = 9999 
        end_node_id = 8888 
        response = await client.get(
            f"/api/v1/routes/summary/{start_node_id}/{end_node_id}"
        )
        assert response.status_code == 404
        assert response.json()["detail"] == 'No path found between nodes 9999 and 8888'

    async def test_get_route_summary_same_node(
        self,
        client: AsyncClient
    ):
        """Test getting route summary from a node to itself returns error"""
        node_id = 32
        response = await client.get(
            f"/api/v1/routes/summary/{node_id}/{node_id}"
         )
        assert response.status_code == 404
        assert response.json()["detail"] == 'No path found between nodes 32 and 32'
