"""Unit tests for dataset metadata service."""

from unittest.mock import AsyncMock, Mock

import pytest

from app.services.metadata import get_dataset_metadata


def _scalar_result(value: int) -> Mock:
    result = Mock()
    result.scalar_one.return_value = value
    return result


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_dataset_metadata_returns_structured_components_with_counts() -> None:
    db = AsyncMock()
    db.execute = AsyncMock(
        side_effect=[
            _scalar_result(7),
            _scalar_result(120),
            _scalar_result(4),
            _scalar_result(245),
        ]
    )

    metadata = await get_dataset_metadata(db, "iggielgn")

    assert metadata is not None
    assert metadata.id == "iggielgn"
    assert metadata.structure.dataset_id == "iggielgn"
    assert metadata.structure.summary.has_nodes is True
    assert metadata.structure.summary.has_edges is True

    components = {component.key: component for component in metadata.structure.components}
    assert components["border_nodes"].record_count == 7
    assert components["generic_nodes"].record_count == 120
    assert components["lng_terminals"].record_count == 4
    assert components["pipeline_segments"].record_count == 245
    assert components["pipeline_segments"].derivation is None


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_dataset_metadata_marks_planned_gem_nodes_as_derived() -> None:
    db = AsyncMock()
    db.execute = AsyncMock(side_effect=[_scalar_result(88)])

    metadata = await get_dataset_metadata(db, "gem_pipelines")

    assert metadata is not None
    components = {component.key: component for component in metadata.structure.components}
    assert components["pipeline_segments"].record_count == 88
    assert components["derived_nodes"].record_count == 0
    assert components["derived_nodes"].storage.source == "derived"
    assert components["derived_nodes"].storage.status == "planned"
    assert components["derived_nodes"].derivation is not None
    assert components["derived_nodes"].derivation.derived_from == ["pipeline_segments"]
    assert components["derived_nodes"].derivation.derived_at is None