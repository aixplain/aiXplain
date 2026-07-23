from aixplain.factories import ModelFactory
from aixplain.enums import DataType, AssetStatus
import pytest


def test_utility_model_status():
    utility_model = None
    try:

        def get_user_location(dummy_input: str, dummy_input2: str) -> str:
            """Get user's city using dummy input"""
            import requests
            import json

            try:
                response = requests.get("http://ip-api.com/json/")
                response.raise_for_status()
                data = response.json()
                location = {"city": data["city"], "latitude": data["lat"], "longitude": data["lon"]}
                return json.dumps(location)
            except Exception as e:
                return json.dumps({"error": str(e)})

        utility_model = ModelFactory.create_utility_model(
            name="Location Utility Test",
            code=get_user_location,
        )

        # Test model creation
        assert utility_model.id is not None
        assert len(utility_model.inputs) == 2
        assert utility_model.inputs[0].name == "dummy_input"
        assert utility_model.inputs[1].name == "dummy_input2"
        assert utility_model.inputs[0].type == DataType.TEXT
        assert utility_model.inputs[1].type == DataType.TEXT

        # Check initial status is DRAFT
        assert utility_model.status == AssetStatus.DRAFT

        # deploy the model
        utility_model.deploy()

        # Check status is now ONBOARDED
        assert utility_model.status == AssetStatus.ONBOARDED

        # try  reinitialize the model this should fail
        # Second deployment attempt - should fail
        utility_model_duplicate = ModelFactory.create_utility_model(
            name="Location Utility Test",  # Same name
            code=get_user_location,
        )

        # Be more specific about the exception you're expecting
        with pytest.raises(Exception, match=".*Utility name already exists*"):
            utility_model_duplicate.deploy()

    finally:
        if utility_model:
            utility_model.delete()
        if utility_model_duplicate:
            utility_model_duplicate.delete()


def test_model_tool_creation():
    from aixplain.factories import AgentFactory
    import warnings

    # Capture warnings during the create_model_tool call
    with warnings.catch_warnings(record=True) as w:
        # Cause all warnings to always be triggered
        warnings.simplefilter("always")
        # Create the model tool
        AgentFactory.create_model_tool(model="6736411cf127849667606689")  # Tavily Search
        # Check that no warnings were raised
        assert len(w) == 0, f"Warning was raised when calling create_model_tool: {[warning.message for warning in w]}"
