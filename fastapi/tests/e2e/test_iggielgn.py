
import pytest
from httpx import AsyncClient


@pytest.mark.e2e
class TestIGGIELGNEndpoints:
    """Test the /api/v1/iggielgn endpoints"""

    async def test_get_generic_nodes(
        self,
        client: AsyncClient
    ):
        """Test getting generic nodes with limit"""
        response = await client.get(
            "/api/v1/iggielgn/nodes?limit=10"
        )

        assert response.status_code == 200
        content = response.json()

        assert content["metadata"] is not None
        assert content["data"] is not None
        assert isinstance(content["data"], list)
        assert len(content["data"]) > 0


        assert content["metadata"]["dataset_id"] == "iggielgn"
        assert content["metadata"]["dataset_name"] == "IGGIELGN - Integrated Gas Grid Infrastructure European Long-Distance Gas Network"
        assert content["metadata"]["source"] == "SciGRID_gas"
        assert content["metadata"]["organization"] == "Institute of Networked Energy Systems, German Aerospace Center (DLR)"
        assert content["metadata"]["license"] == "ODbL-1.0 (Open Database License)"
        assert content["metadata"]["attribution"] == "SciGRID_gas IGGIELGN, Institute of Networked Energy Systems, German Aerospace Center (DLR). Based on OpenStreetMap data © OpenStreetMap contributors."
        assert content["metadata"]["dataset_url"] == "https://www.gas.scigrid.de/"
        assert content["metadata"]["documentation_url"] == "https://www.gas.scigrid.de/downloads.html"

        assert content["metadata"]["record_count"] == 10
        assert len(content["data"]) == 10
        
        expected_fields = {"id", "lat", "lon", "name", "country_code"}
        for item in content["data"]:
            assert expected_fields.issubset(item.keys())


    async def test_get_generic_nodes_country_de(
        self,
        client: AsyncClient,
    ):
        """Test getting generic nodes with country filter and limit"""
        response = await client.get(
            "/api/v1/iggielgn/nodes?limit=20&country=DE"
        )

        assert response.status_code == 200
        content = response.json()

        assert content["metadata"] is not None
        assert content["data"] is not None
        assert isinstance(content["data"], list)
        assert len(content["data"]) > 0


        assert content["metadata"]["dataset_id"] == "iggielgn"
        assert content["metadata"]["dataset_name"] == "IGGIELGN - Integrated Gas Grid Infrastructure European Long-Distance Gas Network"
        assert content["metadata"]["source"] == "SciGRID_gas"
        assert content["metadata"]["organization"] == "Institute of Networked Energy Systems, German Aerospace Center (DLR)"
        assert content["metadata"]["license"] == "ODbL-1.0 (Open Database License)"
        assert content["metadata"]["attribution"] == "SciGRID_gas IGGIELGN, Institute of Networked Energy Systems, German Aerospace Center (DLR). Based on OpenStreetMap data © OpenStreetMap contributors."
        assert content["metadata"]["dataset_url"] == "https://www.gas.scigrid.de/"
        assert content["metadata"]["documentation_url"] == "https://www.gas.scigrid.de/downloads.html"

        assert content["metadata"]["record_count"] == 20
        assert len(content["data"]) == 20
        
        expected_fields = {"id", "lat", "lon", "name", "country_code"}
        for item in content["data"]:
            assert expected_fields.issubset(item.keys())
            assert item["country_code"] == "DE"

    async def test_get_unified_nodes(
        self,
        client: AsyncClient,
    ):
        """Test getting unified nodes with country filter and limit"""
        response = await client.get(
            "/api/v1/iggielgn/nodes-unified?limit=20&country=DE"
        )

        assert response.status_code == 200
        content = response.json()

        assert content["metadata"] is not None
        assert content["data"] is not None
        assert isinstance(content["data"], list)
        assert len(content["data"]) > 0

        assert content["metadata"]["record_count"] == 20
        assert len(content["data"]) == 20
        
        expected_fields = {"id", "lat", "lon", "name", "country_code", "node_type"}
        for item in content["data"]:
            assert expected_fields.issubset(item.keys())
            assert item["country_code"] == "DE"



    async def test_get_border_crossing_nodes(
        self,
        client: AsyncClient,
    ):
        """Test getting border crossing nodes with country filter and limit"""
        response = await client.get(
            "/api/v1/iggielgn/border-crossings?country=DE&limit=21"
        )

        assert response.status_code == 200
        content = response.json()

        assert content["metadata"] is not None
        assert content["data"] is not None
        assert isinstance(content["data"], list)
        assert len(content["data"]) >0      
        assert len(content["data"]) <= 21
        
        assert content["metadata"]["dataset_id"] == "iggielgn"
        assert content["metadata"]["record_count"] <= 21
   
        expected_fields = {"id", "lat", "lon", "name", "country_code", "from_country", "to_country", "from_TSO", "to_TSO"}
        for item in content["data"]:
            assert expected_fields.issubset(item.keys())
            assert item["country_code"] == "DE"


async def test_get_segments(
    client: AsyncClient,
):
    """Test getting segments with country filter and limit"""
    response = await client.get(
        "/api/v1/iggielgn/segments?limit=20&country=DE"
    )

    assert response.status_code == 200
    content = response.json()

    assert content["metadata"] is not None
    assert content["data"] is not None
    assert isinstance(content["data"], list)
    assert len(content["data"]) > 0

    assert content["metadata"]["record_count"] == 20
    assert len(content["data"]) == 20
    
    expected_fields = {"id", "from_node", "to_node", "length_km", "IGGIELGN_id", "country_code_from", "country_code_to", "is_H_gas"}
    for item in content["data"]:
        assert expected_fields.issubset(item.keys())
        assert item["country_code_from"] == "DE" or item["country_code_to"] == "DE"
        assert item["length_km"] > 0 


async def test_get_route_from_nodes(
    client: AsyncClient,
):
    """Test getting route between two nodes"""


    source_node_id, target_node_id = 255, 743

    response = await client.get(
        f"/api/v1/iggielgn/route/{source_node_id}/{target_node_id}"
    )

    assert response.status_code == 200
    content = response.json()

    assert content["source_node_id"] == source_node_id
    assert content["target_node_id"] == target_node_id