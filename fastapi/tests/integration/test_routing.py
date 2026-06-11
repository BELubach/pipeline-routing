"""
Integration tests for routing service layer
Tests the service functions directly without HTTP stack
"""
import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.services import routing as routing_service


@pytest.mark.integration
class TestRoutingShortestPath:

    async def test_db_is_initialized(self, db_session: AsyncSession):
        """Verify database connection and basic query"""
        
        result = await db_session.execute(
            text("SELECT id FROM generic_nodes LIMIT 2")
        )
        nodes = result.fetchall()
        assert len(nodes) > 0, "No nodes found in database"

        
    async def test_find_shortest_path_basic(self, db_session: AsyncSession):
        """Test finding shortest path between two nodes"""
        
        start_node = 32
        end_node = 55
        
        print(f"   Start: {start_node}, End: {end_node}")
        
        path = await routing_service.find_shortest_path(db_session, start_node, end_node)
        
        assert path is not None
        assert isinstance(path, list)
        assert len(path) > 0
        
        first = path[0]
        assert first.seq == 1
        assert first.node_id == start_node
        assert first.total_distance >= 0
        
        last = path[-1]
        assert last.node_id == end_node
        
        print(f"Path found: {len(path)} nodes, {last.total_distance}km")
        

    async def test_find_shortest_path_same_node(self, db_session: AsyncSession):
        """Test routing from a node to itself raises a ValueError"""
        
        node_id = 32
        print(f"   Node: {node_id}")
        
        with pytest.raises(ValueError) as exc_info:
            await routing_service.find_shortest_path(db_session, node_id, node_id)


    async def test_find_shortest_path_nonexistent_nodes(self, db_session: AsyncSession):
        """Test routing with non-existent nodes"""
        
        with pytest.raises(ValueError) as exc_info:
            await routing_service.find_shortest_path(db_session, 999999999, 999999998)
        