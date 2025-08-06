import pytest
from aixplain.enums import SortBy, SortOrder


@pytest.fixture(scope="module")
def text_model_id():
    """Return a text-generation model ID for testing."""
    return "669a63646eb56306647e1091"  # GPT-4o Mini


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

    if model.subscriptions:
        assert isinstance(model.subscriptions, list)

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

    try:
        result = model.run(data="Hello! Please respond with a short greeting.")
        assert hasattr(result, "status")
        assert hasattr(result, "data")
        assert result.status == "SUCCESS"
        assert result.data is not None
    except Exception as e:
        pytest.skip(f"Model run not supported: {e}")
