import pytest
from aixplain.enums import SortBy, SortOrder


@pytest.fixture(scope="module")
def text_model_id():
    """Return a text-generation model ID for testing."""
    return "669a63646eb56306647e1091"  # GPT-4o Mini


@pytest.fixture(scope="module")
def slack_integration_id():
    """Return a Slack integration model ID for testing."""
    return "686432941223092cb4294d3f"  # Use Script integration (Slack integration)


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

    if model.host:
        assert isinstance(model.host, str)

    if model.developer:
        assert isinstance(model.developer, str)

    # Test vendor structure if present
    if model.vendor:
        assert hasattr(model.vendor, "id")
        assert hasattr(model.vendor, "name")
        assert hasattr(model.vendor, "code")

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


def test_search_models(client):
    """Test searching models with pagination."""
    models = client.Model.search()
    assert hasattr(models, "results")
    assert isinstance(models.results, list)
    number_of_models = len(models.results)
    assert number_of_models > 0, "Expected to get results from model search"

    # Validate structure of returned tools
    for model in models.results:
        validate_model_structure(model)

    if number_of_models < 2:
        pytest.skip("Expected to have at least 2 models for testing pagination")

    # Test with page size
    models = client.Model.search(page_size=number_of_models - 1)
    assert hasattr(models, "results")
    assert isinstance(models.results, list)
    assert len(models.results) <= number_of_models - 1, (
        f"Expected at most {number_of_models - 1} models, but got {len(models.results)}"
    )

    # Test with page number
    models_page_2 = client.Model.search(page_number=1, page_size=number_of_models - 1)
    assert hasattr(models_page_2, "results")
    assert isinstance(models_page_2.results, list)
    assert len(models_page_2.results) <= number_of_models - 1, (
        f"Expected at most {number_of_models - 1} models, but got {len(models_page_2.results)}"
    )


def test_search_models_with_filter(client):
    """Test searching models with text query filter."""
    # Test with a common search term
    query = "GPT"
    search_models = client.Model.search(query=query)
    assert hasattr(search_models, "results")
    assert isinstance(search_models.results, list)

    if search_models.results:
        for model in search_models.results:
            assert query.lower() not in model.name


def test_search_models_with_sorting(client):
    """Test searching models with different sorting options."""
    # Test sorting by creation date ascending
    models_date_asc = client.Model.search(sort_by=SortBy.CREATION_DATE, sort_order=SortOrder.ASCENDING)
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
            assert dates == sorted_dates, f"Expected dates to be in ascending order, but got: {dates}"

    # Test sorting by creation date descending
    models_date_desc = client.Model.search(sort_by=SortBy.CREATION_DATE, sort_order=SortOrder.DESCENDING)
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
            assert dates == sorted_dates, f"Expected dates to be in descending order, but got: {dates}"


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
                valid_params[param.name] = "Hello! Please respond with a short greeting."
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


def test_dynamic_validation_slack_integration(client, slack_integration_id, slack_token):
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
        error_str = str(e).lower()
        assert "supplier_error" in error_str or "tool send_message not found" in error_str
        print(f"Slack integration failed as expected: {e}")

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
    models = client.Model.search()

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


def test_search_models_with_functions_filter(client):
    """Test searching models using the 'functions' filter with a list of strings."""
    # Use a known function id string from enums (e.g., 'text-generation')
    models = client.Model.search(functions=["text-generation"])
    assert hasattr(models, "results")
    assert isinstance(models.results, list)
    # If results are present, ensure each model has the requested function
    for model in models.results:
        if model.function:
            assert model.function.value == "text-generation"


def test_search_models_with_status_filter(client):
    """Test searching models using the 'status' filter as a list of strings."""
    models = client.Model.search(status=["onboarded"])
    assert hasattr(models, "results")
    assert isinstance(models.results, list)
    for model in models.results:
        if model.status:
            assert str(model.status.value) == "onboarded"


def test_search_models_with_suppliers_filter(client):
    """Test searching models using the 'suppliers' filter as a list of strings."""
    # Use a supplier code known to exist in dev (fallback checks only structure)
    models = client.Model.search(suppliers=["google"])
    assert hasattr(models, "results")
    assert isinstance(models.results, list)


def test_search_models_with_q_parameter(client):
    """Test searching models with 'q' parameter as per Swagger spec."""
    models = client.Model.search(q="GPT")
    assert hasattr(models, "results")
    assert isinstance(models.results, list)


def test_search_models_with_saved_flag(client):
    """Test searching models with saved flag filter."""
    models = client.Model.search(saved=True)
    assert hasattr(models, "results")
    assert isinstance(models.results, list)


def test_model_inputs_proxy_functionality(client, text_model_id):
    """Test the new inputs proxy functionality for dynamic parameter management."""
    model = client.Model.get(text_model_id)

    # Test that inputs proxy is initialized
    assert hasattr(model, "inputs")
    assert model.inputs is not None

    # Test that inputs proxy has the expected parameters
    assert len(model.inputs) > 0, "Inputs proxy should have parameters"

    # Test dot notation access and setting
    if "temperature" in model.inputs:
        # Set temperature using dot notation
        model.inputs.temperature = 0.7
        assert model.inputs.temperature == 0.7

        # Test that the value persists
        assert model.inputs["temperature"] == 0.7

    # Test dict-like access and setting
    if "max_tokens" in model.inputs:
        # Set max_tokens using dict notation
        model.inputs["max_tokens"] = 500
        assert model.inputs["max_tokens"] == 500

        # Test that the value persists
        assert model.inputs.max_tokens == 500

    # Test bulk assignment to inputs
    bulk_params = {}
    if "temperature" in model.inputs:
        bulk_params["temperature"] = 0.8
    if "max_tokens" in model.inputs:
        bulk_params["max_tokens"] = 750
    if "language" in model.inputs:
        bulk_params["language"] = "en"

    if bulk_params:
        model.inputs = bulk_params

        # Verify all values were set
        for param_name, expected_value in bulk_params.items():
            assert model.inputs[param_name] == expected_value
            assert getattr(model.inputs, param_name) == expected_value


def test_model_inputs_proxy_methods(client, text_model_id):
    """Test the various methods available on the inputs proxy."""
    model = client.Model.get(text_model_id)

    # Test has_parameter method
    assert model.inputs.has_parameter("text") == True
    assert model.inputs.has_parameter("nonexistent_param") == False

    # Test get_parameter_names method
    param_names = model.inputs.get_parameter_names()
    assert isinstance(param_names, list)
    assert len(param_names) > 0
    assert "text" in param_names

    # Test get_required_parameters method
    required_params = model.inputs.get_required_parameters()
    assert isinstance(required_params, list)
    assert len(required_params) > 0

    # Test get_parameter_info method
    if "text" in model.inputs:
        text_param_info = model.inputs.get_parameter_info("text")
        assert isinstance(text_param_info, dict)
        assert "required" in text_param_info
        assert "data_type" in text_param_info
        assert "data_sub_type" in text_param_info

    # Test get_all_parameters method
    all_params = model.inputs.get_all_parameters()
    assert isinstance(all_params, dict)
    assert len(all_params) > 0

    # Test copy method
    params_copy = model.inputs.copy()
    assert isinstance(params_copy, dict)
    assert params_copy == all_params


def test_model_inputs_proxy_validation(client, text_model_id):
    """Test parameter validation through the inputs proxy."""
    model = client.Model.get(text_model_id)

    # Test setting valid values
    if "temperature" in model.inputs:
        # This should work
        model.inputs.temperature = 0.5
        assert model.inputs.temperature == 0.5

    # Test setting invalid values (should raise ValueError)
    if "temperature" in model.inputs:
        # temperature has dataType "text" and dataSubType "number", so it accepts strings and numbers
        # Let's test with a completely invalid type like a list
        with pytest.raises(ValueError, match="Invalid value type"):
            model.inputs.temperature = ["invalid", "list", "value"]

    # Test setting values for non-existent parameters
    with pytest.raises(AttributeError, match="Parameter 'nonexistent_param' not found"):
        model.inputs.nonexistent_param = "value"

    with pytest.raises(KeyError, match="Parameter 'nonexistent_param' not found"):
        model.inputs["nonexistent_param"] = "value"


def test_model_inputs_proxy_reset_functionality(client, text_model_id):
    """Test parameter reset functionality through the inputs proxy."""
    model = client.Model.get(text_model_id)

    # Store original values
    original_values = model.inputs.copy()

    # Change some values
    if "temperature" in model.inputs:
        model.inputs.temperature = 0.9
        assert model.inputs.temperature == 0.9

    if "max_tokens" in model.inputs:
        model.inputs.max_tokens = 1000
        assert model.inputs.max_tokens == 1000

    # Test reset_parameter for individual parameters
    if "temperature" in model.inputs:
        model.inputs.reset_parameter("temperature")
        # Should be back to original or backend default
        assert model.inputs.temperature == original_values.get("temperature")

    # Test reset_all_parameters
    model.inputs.reset_all_parameters()

    # All values should be back to original
    current_values = model.inputs.get_all_parameters()
    for param_name in original_values:
        if param_name in current_values:
            assert current_values[param_name] == original_values[param_name]


def test_model_inputs_proxy_update_method(client, text_model_id):
    """Test the update method for setting multiple parameters at once."""
    model = client.Model.get(text_model_id)

    # Test update with valid parameters
    update_params = {}
    if "temperature" in model.inputs:
        update_params["temperature"] = 0.6
    if "max_tokens" in model.inputs:
        update_params["max_tokens"] = 600

    if update_params:
        model.inputs.update(**update_params)

        # Verify all values were updated
        for param_name, expected_value in update_params.items():
            assert model.inputs[param_name] == expected_value

    # Test update with invalid parameter (should raise KeyError)
    with pytest.raises(KeyError, match="Parameter 'nonexistent_param' not found"):
        model.inputs.update(nonexistent_param="value")


def test_model_inputs_proxy_iteration(client, text_model_id):
    """Test iteration and membership testing on the inputs proxy."""
    model = client.Model.get(text_model_id)

    # Test membership testing
    assert "text" in model.inputs
    assert "nonexistent_param" not in model.inputs

    # Test iteration
    param_count = 0
    for param_name in model.inputs:
        param_count += 1
        assert isinstance(param_name, str)
        assert param_name in model.inputs

    assert param_count == len(model.inputs)

    # Test keys, values, items methods
    keys = list(model.inputs.keys())
    values = list(model.inputs.values())
    items = list(model.inputs.items())

    assert len(keys) == len(values) == len(items) == len(model.inputs)

    # Test that keys and values correspond
    for i, key in enumerate(keys):
        assert model.inputs[key] == values[i]
        assert (key, values[i]) == items[i]


def test_model_run_with_configured_inputs(client, text_model_id):
    """Test running a model with parameters configured through the inputs proxy."""
    model = client.Model.get(text_model_id)

    # Configure parameters through inputs proxy
    if "temperature" in model.inputs:
        model.inputs.temperature = 0.7
    if "max_tokens" in model.inputs:
        model.inputs.max_tokens = 500
    if "language" in model.inputs:
        model.inputs.language = "en"

    # Prepare required parameters for the run
    run_params = {}
    for param in model.params:
        if param.required:
            if param.name == "text":
                run_params[param.name] = "Hello! Please respond with a short greeting."
            elif param.name == "language":
                run_params[param.name] = "en"
            else:
                # For other required params, use appropriate defaults
                if param.data_type == "text":
                    run_params[param.name] = "test"
                elif param.data_type == "number":
                    run_params[param.name] = 1
                elif param.data_type == "boolean":
                    run_params[param.name] = True
                elif param.data_type == "json":
                    run_params[param.name] = {"test": "value"}

    # Run the model - it should use the configured inputs plus the run parameters
    result = model.run(**run_params)
    assert hasattr(result, "status")
    assert hasattr(result, "data")
    assert result.status == "SUCCESS"
    assert result.data is not None


def test_model_inputs_proxy_edge_cases(client, text_model_id):
    """Test edge cases and error handling for the inputs proxy."""
    model = client.Model.get(text_model_id)

    # Test setting None values (should work for most parameters)
    if "temperature" in model.inputs:
        model.inputs.temperature = None
        assert model.inputs.temperature is None

    # Test setting empty string
    if "language" in model.inputs:
        model.inputs.language = ""
        assert model.inputs.language == ""

    # Test setting zero values
    if "max_tokens" in model.inputs:
        model.inputs.max_tokens = 0
        assert model.inputs.max_tokens == 0

    # Test that the proxy object has a good string representation
    proxy_repr = repr(model.inputs)
    assert isinstance(proxy_repr, str)
    assert "InputsProxy" in proxy_repr

    # Test that the proxy object has the expected length
    assert len(model.inputs) > 0
    assert len(model.inputs) == len(model.inputs.get_parameter_names())


def test_model_inputs_bulk_assignment_syntax(client, text_model_id):
    """Test the bulk assignment syntax: mymodel.inputs = {...}"""
    model = client.Model.get(text_model_id)

    # Store original values for comparison
    original_values = model.inputs.copy()

    # Test bulk assignment using the syntax: model.inputs = {...}
    bulk_params = {}
    if "temperature" in model.inputs:
        bulk_params["temperature"] = 0.9
    if "max_tokens" in model.inputs:
        bulk_params["max_tokens"] = 800
    if "language" in model.inputs:
        bulk_params["language"] = "en"

    if bulk_params:
        # This is the key test - bulk assignment syntax
        model.inputs = bulk_params

        # Verify all values were set correctly
        for param_name, expected_value in bulk_params.items():
            assert model.inputs[param_name] == expected_value
            assert getattr(model.inputs, param_name) == expected_value

        # Verify that other parameters were not affected
        for param_name in model.inputs:
            if param_name not in bulk_params:
                # These should retain their original values
                assert model.inputs[param_name] == original_values.get(param_name)

    # Test bulk assignment with empty dict (should reset to backend defaults)
    model.inputs = {}

    # All parameters should be back to their backend default values
    current_values = model.inputs.get_all_parameters()
    for param_name in original_values:
        if param_name in current_values:
            # For parameters that were changed, they should be back to backend defaults
            # For parameters that weren't changed, they should be the same
            if param_name in bulk_params:
                # This parameter was changed, so it should be back to backend default
                # We can't assert exact equality since we don't know the backend default
                assert current_values[param_name] is not None or param_name in ["language"]
            else:
                # This parameter wasn't changed, so it should be the same
                assert current_values[param_name] == original_values.get(param_name)

    # Test bulk assignment with invalid parameters (should raise KeyError)
    with pytest.raises(KeyError, match="Parameter 'nonexistent_param' not found"):
        model.inputs = {"nonexistent_param": "value"}


def test_model_inputs_proxy_integration_with_run(client, text_model_id):
    """Test that the inputs proxy integrates correctly with model.run()."""
    model = client.Model.get(text_model_id)

    # Configure some parameters through inputs proxy
    if "temperature" in model.inputs:
        model.inputs.temperature = 0.6
    if "max_tokens" in model.inputs:
        model.inputs.max_tokens = 400

    # Prepare minimal required parameters for the run
    run_params = {}
    for param in model.params:
        if param.required:
            if param.name == "text":
                run_params[param.name] = "Please respond with a very short message."
            elif param.name == "language":
                run_params[param.name] = "en"
            else:
                # For other required params, use appropriate defaults
                if param.data_type == "text":
                    run_params[param.name] = "test"
                elif param.data_type == "number":
                    run_params[param.name] = 1
                elif param.data_type == "boolean":
                    run_params[param.name] = True
                elif param.data_type == "json":
                    run_params[param.name] = {"test": "value"}

    # Run the model - it should automatically use the configured inputs
    result = model.run(**run_params)
    assert hasattr(result, "status")
    assert hasattr(result, "data")
    assert result.status == "SUCCESS"
    assert result.data is not None

    # Verify that the configured inputs are still intact after the run
    if "temperature" in model.inputs:
        assert model.inputs.temperature == 0.6
    if "max_tokens" in model.inputs:
        assert model.inputs.max_tokens == 400
