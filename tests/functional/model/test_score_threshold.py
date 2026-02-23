"""Test score threshold filtering for IndexModel.search()"""

import pytest
import time
import uuid
from aixplain.factories import IndexFactory
from aixplain.modules.model.record import Record


@pytest.fixture(scope="module")
def setup_test_index():
    """Create an index with test records for score threshold testing."""
    unique_name = f"score_threshold_test_{uuid.uuid4().hex[:8]}"
    index_model = IndexFactory.create(name=unique_name, description="Test index for score threshold")

    # Wait for index to be ready
    time.sleep(5)

    # Add test records with varied content
    test_records = [
        Record(id="1", value="Python programming language tutorial", value_type="text", attributes={"topic": "python"}),
        Record(
            id="2", value="JavaScript web development basics", value_type="text", attributes={"topic": "javascript"}
        ),
        Record(
            id="3", value="Python data science and machine learning", value_type="text", attributes={"topic": "python"}
        ),
        Record(id="4", value="Cloud computing infrastructure", value_type="text", attributes={"topic": "cloud"}),
        Record(id="5", value="Python Flask web framework", value_type="text", attributes={"topic": "python"}),
    ]

    index_model.upsert(test_records)
    time.sleep(10)  # Wait for indexing

    yield index_model

    # Cleanup
    index_model.delete()


def test_score_threshold_zero_returns_all(setup_test_index):
    """With score_threshold=0.0, all matching results should be returned."""
    index_model = setup_test_index
    response = index_model.search("Python", score_threshold=0.0)

    assert response.status == "SUCCESS"
    print(f"\nResults with threshold 0.0: {len(response.details)} records")
    for detail in response.details:
        print(f"  - Score: {detail.get('score', 'N/A')}")


def test_score_threshold_high_returns_none(setup_test_index):
    """With score_threshold=1.0, no results should be returned."""
    index_model = setup_test_index

    response = index_model.search("Python", score_threshold=1.0)
    assert response.status == "SUCCESS"
    print(f"\nResults with threshold 1.0: {len(response.details)} records")
    assert len(response.details) == 0, "No results should match with threshold=1.0"


def test_score_threshold_filters_correctly(setup_test_index):
    """Verify that higher threshold returns fewer or equal results."""
    index_model = setup_test_index

    # Get all results first
    response_all = index_model.search("Python", score_threshold=0.0)
    all_count = len(response_all.details)

    # Get filtered results with medium threshold
    response_filtered = index_model.search("Python", score_threshold=0.5)
    filtered_count = len(response_filtered.details)

    print(f"\nAll results (threshold=0.0): {all_count}")
    print(f"Filtered results (threshold=0.5): {filtered_count}")

    # Filtered count should be <= all count
    assert filtered_count <= all_count


def test_score_threshold_with_filter(setup_test_index):
    """Test score_threshold combined with filters."""
    from aixplain.modules.model.index_model import IndexFilter, IndexFilterOperator

    index_model = setup_test_index

    # Search with filter only (no threshold)
    filter_ = IndexFilter(field="topic", value="python", operator=IndexFilterOperator.EQUALS)
    response = index_model.search("Python", filters=[filter_], score_threshold=0.0)
    assert response.status == "SUCCESS"
    filtered_count = len(response.details)
    print(f"\nResults with filter only (threshold=0.0): {filtered_count}")

    # Search with filter AND high threshold - should return 0
    response = index_model.search("Python", filters=[filter_], score_threshold=1.0)
    assert response.status == "SUCCESS"
    print(f"Results with filter + threshold=1.0: {len(response.details)}")
    assert len(response.details) == 0


def test_score_threshold_with_filter_medium(setup_test_index):
    """Test score_threshold with filter at medium threshold."""
    from aixplain.modules.model.index_model import IndexFilter, IndexFilterOperator

    index_model = setup_test_index

    filter_ = IndexFilter(field="topic", value="python", operator=IndexFilterOperator.EQUALS)

    # Get all filtered results
    response_all = index_model.search("Python", filters=[filter_], score_threshold=0.0)
    all_count = len(response_all.details)

    # Get filtered results with medium threshold
    response_filtered = index_model.search("Python", filters=[filter_], score_threshold=0.8)
    filtered_count = len(response_filtered.details)

    print(f"\nFiltered results (threshold=0.0): {all_count}")
    print(f"Filtered results (threshold=0.8): {filtered_count}")

    # Higher threshold should return fewer or equal results
    assert filtered_count <= all_count


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
