from unittest.mock import Mock
from dataclasses import dataclass
from dataclasses_json import dataclass_json
from aixplain.v2.resource import BaseResource


@dataclass_json
@dataclass
class MockResource(BaseResource):
    """Mock resource for state tracking tests."""

    id: str = ""
    name: str = ""
    description: str = ""
    value: int = 0

    def __post_init__(self):
        """Initialize required fields after dataclass initialization."""
        if not hasattr(self, "context"):
            self.context = None
        if not hasattr(self, "RESOURCE_PATH"):
            self.RESOURCE_PATH = ""
        if not hasattr(self, "_saved_state"):
            self._saved_state = None


class TestStateTracking:
    """Test suite for state tracking functionality."""

    def test_new_resource_is_modified(self):
        """Test that a new resource is considered modified."""
        resource = MockResource(
            id="test-123",
            name="Test Resource",
            description="Test Description",
            value=42,
        )

        assert resource.is_modified is True
        assert resource._saved_state is None

    def test_resource_after_save(self):
        """Test that a resource is not modified after save."""
        resource = MockResource(
            id="test-123",
            name="Test Resource",
            description="Test Description",
            value=42,
        )

        # Simulate save operation
        resource._update_saved_state()

        assert resource.is_modified is False
        assert resource._saved_state is not None
        assert resource._saved_state == {
            "id": "test-123",
            "name": "Test Resource",
            "description": "Test Description",
            "value": 42,
            "path": None,
        }

    def test_resource_modification_detection(self):
        """Test that modifications are detected correctly."""
        resource = MockResource(
            id="test-123",
            name="Test Resource",
            description="Test Description",
            value=42,
        )

        # Set initial saved state
        resource._update_saved_state()
        assert resource.is_modified is False

        # Modify a field
        resource.name = "Modified Name"
        assert resource.is_modified is True

        # Modify another field
        resource.value = 100
        assert resource.is_modified is True

        # Reset to original state
        resource.name = "Test Resource"
        resource.value = 42
        assert resource.is_modified is False

    def test_multiple_modifications(self):
        """Test multiple field modifications."""
        resource = MockResource(
            id="test-123",
            name="Test Resource",
            description="Test Description",
            value=42,
        )

        resource._update_saved_state()
        assert resource.is_modified is False

        # Modify multiple fields
        resource.name = "New Name"
        resource.description = "New Description"
        resource.value = 100

        assert resource.is_modified is True

        # Check current state
        current_state = resource._get_serializable_state()
        expected_state = {
            "id": "test-123",
            "name": "New Name",
            "description": "New Description",
            "value": 100,
            "path": None,
        }
        assert current_state == expected_state

    def test_save_operation_updates_state(self):
        """Test that save operation updates the saved state."""
        resource = MockResource(
            id="test-123",
            name="Test Resource",
            description="Test Description",
            value=42,
        )

        # Modify the resource
        resource.name = "Modified Name"
        assert resource.is_modified is True

        # Simulate save operation
        resource._update_saved_state()
        assert resource.is_modified is False

        # Verify saved state matches current state
        current_state = resource._get_serializable_state()
        assert resource._saved_state == current_state

    def test_internal_fields_excluded_from_comparison(self):
        """Test that internal fields are excluded from state comparison."""
        resource = MockResource(
            id="test-123",
            name="Test Resource",
            description="Test Description",
            value=42,
        )

        # Set context and other internal fields
        resource.context = Mock()
        resource.RESOURCE_PATH = "test/path"

        # Get serializable state
        state = resource._get_serializable_state()

        # Internal fields should be excluded
        assert "context" not in state
        assert "RESOURCE_PATH" not in state
        assert "_saved_state" not in state

        # Only data fields should be included
        expected_fields = {"id", "name", "description", "value", "path"}
        assert set(state.keys()) == expected_fields

    def test_empty_resource_state(self):
        """Test state tracking with empty/default values."""
        resource = MockResource()

        # New resource should be modified
        assert resource.is_modified is True

        # Set saved state
        resource._update_saved_state()
        assert resource.is_modified is False

        # Default state should be empty strings and 0
        expected_state = {
            "id": "",
            "name": "",
            "description": "",
            "value": 0,
            "path": None,
        }
        assert resource._saved_state == expected_state

    def test_state_consistency_after_modifications(self):
        """Test that state remains consistent after multiple modifications."""
        resource = MockResource(
            id="test-123",
            name="Test Resource",
            description="Test Description",
            value=42,
        )

        # Set initial saved state
        resource._update_saved_state()
        initial_saved_state = resource._saved_state.copy()

        # Make modifications
        resource.name = "Modified Name"
        resource.value = 100

        # Verify current state reflects changes
        current_state = resource._get_serializable_state()
        assert current_state["name"] == "Modified Name"
        assert current_state["value"] == 100

        # Verify saved state remains unchanged
        assert resource._saved_state == initial_saved_state

        # Reset to original state
        resource.name = "Test Resource"
        resource.value = 42

        # Should no longer be modified
        assert resource.is_modified is False
