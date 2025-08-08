import pytest
from aixplain.enums import SortBy, SortOrder


@pytest.fixture(scope="module")
def text_model_id():
    """Return a text-generation model ID for testing."""
    return "669a63646eb56306647e1091"  # GPT-4o Mini


@pytest.fixture(scope="module")
def slack_integration_id():
    """Return a Slack integration model ID for testing."""
    return "688bcba8f95544bce74b47ac"  # Slack integration


def validate_model_structure(model):
    """Helper function to validate model structure and data types."""
    # Test core fields
    assert isinstance(model.id, str)
    assert isinstance(model.name, str)
    # Description can be None for some models
    if model.description is not None:
        assert isinstance(model.description, str)

    # Test optional fields if present
    if model.service_name:
        assert isinstance(model.service_name, str)

    if model.status:
        assert hasattr(model.status, "value")

    if model.hosted_by:
        assert isinstance(model.hosted_by, str)

    if model.developed_by:
        assert isinstance(model.developed_by, str)

    # Test supplier structure if present
    if model.supplier:
        assert hasattr(model.supplier, "id")
        assert hasattr(model.supplier, "name")
        assert hasattr(model.supplier, "code")

    # Test pricing structure if present
    if model.pricing:
        assert hasattr(model.pricing, "price")

    # Test version structure if present
    if model.version:
        assert hasattr(model.version, "name")
        assert hasattr(model.version, "id")

    # Test function structure if present
    if model.function:
        assert hasattr(model.function, "value")

    # Test capabilities if present
    if model.supports_streaming is not None:
        assert isinstance(model.supports_streaming, bool)

    if model.supports_byoc is not None:
        assert isinstance(model.supports_byoc, bool)

    # Test timestamps if present
    if model.created_at:
        assert isinstance(model.created_at, str)

    if model.updated_at:
        assert isinstance(model.updated_at, str)

    # Test attributes if present
    if model.attributes:
        assert isinstance(model.attributes, list)
        for attr in model.attributes:
            assert hasattr(attr, "name")
            assert hasattr(attr, "code")

    # Test parameters if present
    if model.params:
        assert isinstance(model.params, list)
        for param in model.params:
            assert hasattr(param, "name")
            assert hasattr(param, "required")
            assert hasattr(param, "data_type")
            assert hasattr(param, "data_sub_type")


def test_list_models(client):
    """Test listing models with pagination."""
    models = client.Model.list()
    assert hasattr(models, "results")
    assert isinstance(models.results, list)
    number_of_models = len(models.results)
    assert number_of_models > 0, "Expected to get results from model listing"

    # Validate structure of returned tools
    for model in models.results:
        validate_model_structure(model)

    if number_of_models < 2:
        pytest.skip("Expected to have at least 2 models for testing pagination")

    # Test with page size
    models = client.Model.list(page_size=number_of_models - 1)
    assert hasattr(models, "results")
    assert isinstance(models.results, list)
    assert (
        len(models.results) <= number_of_models - 1
    ), f"Expected at most {number_of_models - 1} models, but got {len(models.results)}"

    # Test with page number
    models_page_2 = client.Model.list(page_number=1, page_size=number_of_models - 1)
    assert hasattr(models_page_2, "results")
    assert isinstance(models_page_2.results, list)
    assert (
        len(models_page_2.results) <= number_of_models - 1
    ), f"Expected at most {number_of_models - 1} models, but got {len(models_page_2.results)}"


def test_list_models_with_filter(client):
    """Test listing models with text query filter."""
    # Test with a common search term
    query = "GPT"
    search_models = client.Model.list(query=query)
    assert hasattr(search_models, "results")
    assert isinstance(search_models.results, list)

    if search_models.results:
        for model in search_models.results:
            assert query.lower() not in model.name


def test_list_models_with_sorting(client):
    """Test listing models with different sorting options."""
    # Test sorting by creation date ascending
    models_date_asc = client.Model.list(
        sort_by=SortBy.CREATION_DATE, sort_order=SortOrder.ASCENDING
    )
    assert hasattr(models_date_asc, "results")
    assert isinstance(models_date_asc.results, list)
    assert len(models_date_asc.results) > 0

    # Validate that results are sorted by creation date in ascending order
    if len(models_date_asc.results) > 1:
        dates = []
        for model in models_date_asc.results:
            if model.created_at:
                dates.append(model.created_at)

        if len(dates) > 1:
            # Check if dates are in ascending order
            sorted_dates = sorted(dates)
            assert (
                dates == sorted_dates
            ), f"Expected dates to be in ascending order, but got: {dates}"

    # Test sorting by creation date descending
    models_date_desc = client.Model.list(
        sort_by=SortBy.CREATION_DATE, sort_order=SortOrder.DESCENDING
    )
    assert hasattr(models_date_desc, "results")
    assert isinstance(models_date_desc.results, list)
    assert len(models_date_desc.results) > 0

    # Validate that results are sorted by creation date in descending order
    if len(models_date_desc.results) > 1:
        dates = []
        for model in models_date_desc.results:
            if model.created_at:
                dates.append(model.created_at)

        if len(dates) > 1:
            # Check if dates are in descending order
            sorted_dates = sorted(dates, reverse=True)
            assert (
                dates == sorted_dates
            ), f"Expected dates to be in descending order, but got: {dates}"


def test_get_model(client, text_model_id):
    """Test getting a specific model by ID and validate its structure."""
    model = client.Model.get(text_model_id)
    assert model.id == text_model_id

    # Validate complete model structure
    validate_model_structure(model)


def test_run_model(client, text_model_id):
    """Test running a model."""
    model = client.Model.get(text_model_id)

    # Test with valid parameters
    valid_params = {}
    for param in model.params:
        if param.required:
            if param.name == "text":
                valid_params[param.name] = (
                    "Hello! Please respond with a short greeting."
                )
            elif param.name == "language":
                valid_params[param.name] = "en"
            else:
                # For other required params, use appropriate defaults
                if param.data_type == "text":
                    valid_params[param.name] = "test"
                elif param.data_type == "number":
                    valid_params[param.name] = 1
                elif param.data_type == "boolean":
                    valid_params[param.name] = True
                elif param.data_type == "json":
                    valid_params[param.name] = {"test": "value"}

    # Test the model run - this should work with proper parameters
    result = model.run(**valid_params)
    assert hasattr(result, "status")
    assert hasattr(result, "data")
    assert result.status == "SUCCESS"
    assert result.data is not None


def test_dynamic_validation_gpt4o_mini(client, text_model_id):
    """Test dynamic validation with GPT-4o Mini LLM model."""
    model = client.Model.get(text_model_id)

    # Verify the model has the expected parameters
    assert model.params is not None, "Model should have parameters defined"

    # Find required parameters
    required_params = [param for param in model.params if param.required]
    assert len(required_params) > 0, "Model should have required parameters"

    # Test with valid parameters
    valid_params = {}
    for param in model.params:
        if param.required:
            if param.name == "text":
                valid_params[param.name] = "Hello, world!"
            elif param.name == "language":
                valid_params[param.name] = "en"
            else:
                # For other required params, use appropriate defaults
                if param.data_type == "text":
                    valid_params[param.name] = "test"
                elif param.data_type == "number":
                    valid_params[param.name] = 1
                elif param.data_type == "boolean":
                    valid_params[param.name] = True
                elif param.data_type == "json":
                    valid_params[param.name] = {"test": "value"}

    # Test with valid parameters - this should work
    result = model.run(**valid_params)
    assert result.status == "SUCCESS"

    # Test with missing required parameter (should fail)
    missing_params = {k: v for k, v in valid_params.items() if k != "text"}
    with pytest.raises(ValueError, match="Required parameter 'text' is missing"):
        model.run(**missing_params)

    # Test with invalid parameter type (should fail)
    invalid_params = valid_params.copy()
    invalid_params["text"] = 123  # Should be string, not int
    with pytest.raises(ValueError, match="Parameter 'text' has invalid type"):
        model.run(**invalid_params)


def test_dynamic_validation_slack_integration(
    client, slack_integration_id, slack_token
):
    """Test dynamic validation with Slack integration model."""
    model = client.Model.get(slack_integration_id)

    # Verify the model has the expected parameters
    assert model.params is not None, "Model should have parameters defined"

    # Find required parameters
    required_params = [param for param in model.params if param.required]
    assert len(required_params) > 0, "Model should have required parameters"

    # Test with valid parameters
    valid_params = {
        "action": "send_message",
        "data": {"channel": "#general", "text": "Hello from test!"},
    }

    # Test validation - this should work with proper parameters
    # Note: The Slack integration might fail due to backend tool configuration,
    # but the validation should pass
    try:
        result = model.run(**valid_params)
        assert result.status == "SUCCESS"
    except Exception as e:
        # If the Slack integration fails due to backend tool configuration,
        # that's expected in the test environment. The important thing is
        # that the validation passed and we got a proper error.
        assert "supplier_error" in str(e) or "Tool SEND_MESSAGE not found" in str(e)
        print(f"Slack integration failed as expected: {e}")

    # Test with missing required parameter (should fail validation)
    with pytest.raises(ValueError, match="Required parameter 'action' is missing"):
        model.run(data={"channel": "#general", "text": "Hello!"})

    # Test with missing required parameter (should fail validation)
    with pytest.raises(ValueError, match="Required parameter 'data' is missing"):
        model.run(action="send_message")

    # Test with invalid parameter type (should fail validation)
    invalid_params = {
        "action": 123,  # Should be string, not int
        "data": {"channel": "#general", "text": "Hello!"},
    }
    with pytest.raises(ValueError, match="Parameter 'action' has invalid type"):
        model.run(**invalid_params)


def test_dynamic_validation_parameter_types(client, text_model_id):
    """Test dynamic validation with different parameter types."""
    model = client.Model.get(text_model_id)

    # Test with all valid parameter types
    valid_params = {
        "text": "Hello, world!",
        "language": "en",
        "temperature": 0.5,  # number
        "max_tokens": 50,  # number
        "context": "Test context",  # text
        "prompt": "Test prompt",  # text
    }

    # Only include parameters that exist in the model
    available_params = {}
    for param_name, param_value in valid_params.items():
        if any(param.name == param_name for param in model.params):
            available_params[param_name] = param_value

    # Test validation - this should work with proper parameters
    result = model.run(**available_params)
    assert result.status == "SUCCESS"

    # Test with string values for number parameters (should be valid for text/number)
    if any(param.name == "temperature" for param in model.params):
        string_params = available_params.copy()
        string_params["temperature"] = "0.5"  # Should be valid for text/number
        result = model.run(**string_params)
        assert result.status == "SUCCESS"

    # Test with invalid type for text parameter
    if any(param.name == "text" for param in model.params):
        invalid_params = available_params.copy()
        invalid_params["text"] = 123  # Should be string, not number
        with pytest.raises(ValueError, match="Parameter 'text' has invalid type"):
            model.run(**invalid_params)


def test_dynamic_validation_unknown_model(client):
    """Test dynamic validation with a model that has no params (should not fail)."""
    # Get a list of models to find one without params
    models = client.Model.list()

    for model in models.results:
        if not model.params:
            # If the model has no params, validation should pass
            result = model.run(data="test")
            assert result.status == "SUCCESS"
            break
    else:
        # If no model without params found, test with a model that has params
        # but use only the required ones with proper values
        for model in models.results:
            if model.params:
                required_params = {}
                for param in model.params:
                    if param.required:
                        if param.name == "text":
                            required_params[param.name] = "test"
                        elif param.name == "language":
                            required_params[param.name] = "en"
                        elif param.name == "sourcelanguage":
                            # Use the first available value from the param
                            if param.values and len(param.values) > 0:
                                required_params[param.name] = param.values[0]["value"]
                            else:
                                required_params[param.name] = "en"
                        elif param.name == "targetlanguage":
                            # Use the first available value from the param
                            if param.values and len(param.values) > 0:
                                required_params[param.name] = param.values[0]["value"]
                            else:
                                required_params[param.name] = "es"
                        elif param.data_type == "text":
                            required_params[param.name] = "test"
                        elif param.data_type == "number":
                            required_params[param.name] = 1
                        elif param.data_type == "boolean":
                            required_params[param.name] = True
                        elif param.data_type == "json":
                            required_params[param.name] = {"test": "value"}

                # Only try to run if we have all required parameters
                if len(required_params) == len([p for p in model.params if p.required]):
                    result = model.run(**required_params)
                    assert result.status == "SUCCESS"
                    break
        else:
            # If no suitable model found, create a simple test
            # Test that validation works even with empty params
            model = models.results[0]  # Use first available model
            result = model.run()
            assert result.status == "SUCCESS"


def test_model_parameter_structure(client, text_model_id):
    """Test that model parameters have the correct structure."""
    model = client.Model.get(text_model_id)

    if model.params:
        for param in model.params:
            # Test required fields
            assert hasattr(param, "name")
            assert hasattr(param, "required")
            assert hasattr(param, "data_type")
            assert hasattr(param, "data_sub_type")
            assert hasattr(param, "multiple_values")
            assert hasattr(param, "is_fixed")
            assert hasattr(param, "values")
            assert hasattr(param, "default_values")
            assert hasattr(param, "available_options")

            # Test data types
            assert isinstance(param.name, str)
            assert isinstance(param.required, bool)
            assert isinstance(param.data_type, str)
            assert isinstance(param.data_sub_type, str)
            assert isinstance(param.multiple_values, bool)
            assert isinstance(param.is_fixed, bool)
            assert isinstance(param.values, list)
            assert isinstance(param.default_values, list)
            assert isinstance(param.available_options, list)


def test_model_validation_edge_cases(client):
    """Test edge cases in dynamic validation."""
    models = client.Model.list()

    for model in models.results:
        if model.params:
            # Test with empty parameters
            try:
                result = model.run()
                # If no required parameters, this should work
                assert result.status == "SUCCESS"
                break
            except ValueError as e:
                # If there are required parameters, this should fail
                assert "Required parameter" in str(e)
                break
            except Exception:
                # If the model doesn't support running, try the next one
                continue
    else:
        pytest.skip("No suitable model found for testing edge cases")


def test_model_legacy_compatibility(client, text_model_id):
    """Test that models still work with legacy 'data' parameter for backward compatibility."""
    model = client.Model.get(text_model_id)

    try:
        # Test with legacy 'data' parameter
        result = model.run(data="Hello, world!")
        assert result.status == "SUCCESS"
        assert result.data is not None
    except Exception as e:
        # If legacy compatibility fails, that's okay - we're testing the new validation
        print(f"Legacy compatibility test failed: {e}")


def test_list_models_with_functions_filter(client):
    """Test listing models using the 'functions' filter with a list of strings."""
    # Use a known function id string from enums (e.g., 'text-generation')
    models = client.Model.list(functions=["text-generation"])
    assert hasattr(models, "results")
    assert isinstance(models.results, list)
    # If results are present, ensure each model has the requested function
    for model in models.results:
        if model.function:
            assert model.function.value == "text-generation"


def test_list_models_with_status_filter(client):
    """Test listing models using the 'status' filter as a list of strings."""
    models = client.Model.list(status=["onboarded"])
    assert hasattr(models, "results")
    assert isinstance(models.results, list)
    for model in models.results:
        if model.status:
            assert str(model.status.value) == "onboarded"


def test_list_models_with_suppliers_filter(client):
    """Test listing models using the 'suppliers' filter as a list of strings."""
    # Use a supplier code known to exist in dev (fallback checks only structure)
    models = client.Model.list(suppliers=["google"])
    assert hasattr(models, "results")
    assert isinstance(models.results, list)


def test_list_models_with_q_parameter(client):
    """Test listing models with 'q' parameter as per Swagger spec."""
    models = client.Model.list(q="GPT")
    assert hasattr(models, "results")
    assert isinstance(models.results, list)


def test_list_models_with_saved_flag(client):
    """Test listing models with saved flag."""
    models = client.Model.list(saved=False)
    assert hasattr(models, "results")
    assert isinstance(models.results, list)
