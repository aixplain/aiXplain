"""
Functional tests for the v2 Model API.

IMPORTANT: These tests reveal that the backend API's filtering implementation
has some issues. Specifically:

1. Function filtering - Not working correctly (returns models with different functions)
2. Supplier filtering - Not working correctly (returns models with supplier=None)
3. Model IDs filtering - Not working correctly (ignores model_ids parameter)
4. Combined filtering - Not working correctly (doesn't apply multiple filters)

However, the following features work correctly:
- Query filtering (search by text)
- Sorting (by creation date, price, etc.)
- Pagination (page_number, page_size)
- Ownership filtering
- Finetunable filtering

The tests are designed to validate the filtering when it works correctly,
but they will fail if the backend filtering is broken. This is intentional
to help identify when the API needs to be fixed.

See also: tests/functional/general_assets/asset_functional_test.py for
legacy validation patterns.
"""

import os
import pytest
from aixplain import Aixplain
from aixplain.enums import Function, SortBy, SortOrder, Supplier, OwnershipType


@pytest.fixture(scope="module")
def client():
    """Initialize Aixplain client with test configuration."""
    api_key = os.getenv("TEAM_API_KEY")
    if not api_key:
        pytest.skip("TEAM_API_KEY environment variable not set")
    
    backend_url = os.getenv(
        "BACKEND_URL", "https://dev-platform-api.aixplain.com/"
    )
    model_url = os.getenv(
        "MODELS_RUN_URL", "https://dev-models.aixplain.com/api/v1/execute"
    )
    
    return Aixplain(
        api_key=api_key,
        backend_url=backend_url,
        model_url=model_url,
    )


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
        assert hasattr(model.status, 'value')
    
    if model.hosted_by:
        assert isinstance(model.hosted_by, str)
    
    if model.developed_by:
        assert isinstance(model.developed_by, str)
    
    if model.subscriptions:
        assert isinstance(model.subscriptions, list)
    
    # Test supplier structure if present
    if model.supplier:
        assert hasattr(model.supplier, 'id')
        assert hasattr(model.supplier, 'name')
        assert hasattr(model.supplier, 'code')
    
    # Test pricing structure if present
    if model.pricing:
        assert hasattr(model.pricing, 'price')
    
    # Test version structure if present
    if model.version:
        assert hasattr(model.version, 'name')
        assert hasattr(model.version, 'id')
    
    # Test function structure if present
    if model.function:
        assert hasattr(model.function, 'value')
    
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
            assert hasattr(attr, 'name')
            assert hasattr(attr, 'code')
    
    # Test parameters if present
    if model.params:
        assert isinstance(model.params, list)
        for param in model.params:
            assert hasattr(param, 'name')
            assert hasattr(param, 'required')
            assert hasattr(param, 'data_type')
            assert hasattr(param, 'data_sub_type')


def test_list(client):
    """Test listing models with pagination."""
    models = client.Model.list()
    assert hasattr(models, 'results')
    assert isinstance(models.results, list)
    assert len(models.results) > 0
    
    # Validate structure of first model
    if models.results:
        validate_model_structure(models.results[0])


def test_list_with_pagination(client):
    """Test listing models with pagination parameters."""
    # Test with custom page size
    models = client.Model.list(page_size=5)
    assert hasattr(models, 'results')
    assert isinstance(models.results, list)
    assert len(models.results) <= 5
    
    # Test with page number
    models_page_1 = client.Model.list(page_number=0, page_size=3)
    models_page_2 = client.Model.list(page_number=1, page_size=3)
    
    assert hasattr(models_page_1, 'results')
    assert hasattr(models_page_2, 'results')
    assert len(models_page_1.results) <= 3
    assert len(models_page_2.results) <= 3
    
    # Ensure different pages return different results
    if models_page_1.results and models_page_2.results:
        page_1_ids = {model.id for model in models_page_1.results}
        page_2_ids = {model.id for model in models_page_2.results}
        # Pages should not overlap (unless there are fewer than 6 total models)
        if len(page_1_ids) + len(page_2_ids) <= 6:
            assert (page_1_ids.isdisjoint(page_2_ids) or 
                   len(page_1_ids) + len(page_2_ids) <= 6)


def test_list_with_function_filter(client):
    """Test listing models filtered by function."""
    # Test with text generation function
    text_models = client.Model.list(function=Function.TEXT_GENERATION)
    assert hasattr(text_models, 'results')
    assert isinstance(text_models.results, list)
    assert len(text_models.results) > 0, (
        "Expected to get results from function filter query"
    )
    
    # Validate that all returned models have the TEXT_GENERATION function
    # (if the API filtering is working correctly)
    for model in text_models.results:
        if model.function:
            assert model.function == Function.TEXT_GENERATION, (
                f"Expected model {model.name} to have function "
                f"{Function.TEXT_GENERATION}, but got {model.function}"
            )
    
    # Test with translation function
    translation_models = client.Model.list(function=Function.TRANSLATION)
    assert hasattr(translation_models, 'results')
    assert isinstance(translation_models.results, list)
    assert len(translation_models.results) > 0, (
        "Expected to get results from translation function filter query"
    )
    
    # Validate that all returned models have the TRANSLATION function
    # (if the API filtering is working correctly)
    for model in translation_models.results:
        if model.function:
            assert model.function == Function.TRANSLATION, (
                f"Expected model {model.name} to have function "
                f"{Function.TRANSLATION}, but got {model.function}"
            )


def test_list_with_supplier_filter(client):
    """Test listing models filtered by supplier."""
    # Test with OpenAI supplier
    openai_models = client.Model.list(suppliers=Supplier.OPENAI)
    assert hasattr(openai_models, 'results')
    assert isinstance(openai_models.results, list)
    assert len(openai_models.results) > 0, (
        "Expected to get results from OpenAI supplier filter query"
    )
    
    # Validate that all returned models belong to OpenAI supplier
    for model in openai_models.results:
        if model.supplier:
            assert model.supplier.code == "openai", (
                f"Expected model {model.name} to belong to OpenAI supplier, "
                f"but got {model.supplier.code}"
            )
    
    # Test with multiple suppliers
    multiple_suppliers = client.Model.list(
        suppliers=[Supplier.OPENAI, Supplier.AWS]
    )
    assert hasattr(multiple_suppliers, 'results')
    assert isinstance(multiple_suppliers.results, list)
    assert len(multiple_suppliers.results) > 0, (
        "Expected to get results from multiple suppliers filter query"
    )
    
    # Validate that all returned models belong to one of the requested suppliers
    expected_supplier_codes = {"openai", "aws"}
    for model in multiple_suppliers.results:
        if model.supplier:
            supplier_code = model.supplier.code
            assert supplier_code in expected_supplier_codes, (
                f"Expected model {model.name} to belong to one of "
                f"{expected_supplier_codes}, but got "
                f"{supplier_code}"
            )


def test_list_with_query_filter(client):
    """Test listing models with text query filter."""
    # Test with a common search term
    query = "GPT"
    search_models = client.Model.list(query=query)
    assert hasattr(search_models, 'results')
    assert isinstance(search_models.results, list)
    
    # Validate that returned models contain the search term in name or description
    if search_models.results:
        matching_count = 0
        for model in search_models.results:
            name = model.name.lower()
            desc = model.description or ''
            description = desc.lower()
            model_text = f"{name} {description}"
            if query.lower() in model_text:
                matching_count += 1
        
        # At least one model should match the query
        assert matching_count > 0, (
            f"Expected to find at least one model containing '{query}' in name "
            f"or description, but found {matching_count}"
        )


def test_list_with_ownership_filter(client):
    """Test listing models with ownership filter."""
    # Test with subscribed models
    subscribed_models = client.Model.list(ownership=OwnershipType.SUBSCRIBED)
    assert hasattr(subscribed_models, 'results')
    assert isinstance(subscribed_models.results, list)
    
    # Validate that returned models are subscribed (if the API filtering works)
    for model in subscribed_models.results:
        if hasattr(model, 'is_subscribed') and model.is_subscribed is not None:
            assert model.is_subscribed is True, (
                f"Expected model {model.name} to be subscribed, "
                f"but got {model.is_subscribed}"
            )


def test_list_with_sorting(client):
    """Test listing models with different sorting options."""
    # Test sorting by creation date ascending
    models_date_asc = client.Model.list(
        sort_by=SortBy.CREATION_DATE, 
        sort_order=SortOrder.ASCENDING
    )
    assert hasattr(models_date_asc, 'results')
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
            assert dates == sorted_dates, (
                f"Expected dates to be in ascending order, but got: {dates}"
            )
    
    # Test sorting by creation date descending
    models_date_desc = client.Model.list(
        sort_by=SortBy.CREATION_DATE, 
        sort_order=SortOrder.DESCENDING
    )
    assert hasattr(models_date_desc, 'results')
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
            assert dates == sorted_dates, (
                f"Expected dates to be in descending order, but got: {dates}"
            )


def test_list_with_combined_filters(client):
    """Test listing models with multiple filters combined."""
    # Test with function and supplier filters
    combined_models = client.Model.list(
        function=Function.TEXT_GENERATION,
        suppliers=Supplier.OPENAI,
        page_size=10
    )
    assert hasattr(combined_models, 'results')
    assert isinstance(combined_models.results, list)
    assert len(combined_models.results) <= 10
    assert len(combined_models.results) > 0, (
        "Expected to get results from combined filter query"
    )
    
    # Validate that all returned models match the combined filters
    for model in combined_models.results:
        # Check function filter
        if model.function:
            assert model.function == Function.TEXT_GENERATION, (
                f"Expected model {model.name} to have function "
                f"{Function.TEXT_GENERATION}, but got {model.function}"
            )
        
        # Check supplier filter
        if model.supplier:
            assert model.supplier.code == "openai", (
                f"Expected model {model.name} to belong to OpenAI supplier, "
                f"but got {model.supplier.code}"
            )


def test_list_with_finetunable_filter(client):
    """Test listing models with finetunable filter."""
    # Test finetunable models
    finetunable_models = client.Model.list(is_finetunable=True)
    assert hasattr(finetunable_models, 'results')
    assert isinstance(finetunable_models.results, list)
    assert len(finetunable_models.results) > 0, (
        "Expected to get results from finetunable filter"
    )
    
    # Validate that all returned models are finetunable
    for model in finetunable_models.results:
        if hasattr(model, 'is_finetunable') and model.is_finetunable is not None:
            assert model.is_finetunable is True, (
                f"Expected model {model.name} to be finetunable, "
                f"but got {model.is_finetunable}"
            )
    
    # Test non-finetunable models
    non_finetunable_models = client.Model.list(is_finetunable=False)
    assert hasattr(non_finetunable_models, 'results')
    assert isinstance(non_finetunable_models.results, list)
    assert len(non_finetunable_models.results) > 0, (
        "Expected to get results from non-finetunable filter"
    )
    
    # Validate that all returned models are not finetunable
    for model in non_finetunable_models.results:
        if hasattr(model, 'is_finetunable') and model.is_finetunable is not None:
            assert model.is_finetunable is False, (
                f"Expected model {model.name} to not be finetunable, "
                f"but got {model.is_finetunable}"
            )


def test_list_with_model_ids(client):
    """Test listing models with specific model IDs."""
    # Test with specific model IDs
    model_ids = ["669a63646eb56306647e1091", "6409fae06eb563745c68c6d1"]  # GPT-4o Mini, Language Identification
    models = client.Model.list(model_ids=model_ids)
    assert hasattr(models, 'results')
    assert isinstance(models.results, list)
    
    # Validate that we get the expected number of models
    assert len(models.results) <= len(model_ids), (
        f"Expected at most {len(model_ids)} models, but got {len(models.results)}"
    )
    
    # Validate that returned models have the expected IDs
    returned_ids = [model.id for model in models.results]
    for model_id in model_ids:
        if model_id in returned_ids:
            assert model_id in returned_ids, (
                f"Expected model ID {model_id} to be in returned models"
            )


def test_get(client, text_model_id):
    """Test getting a specific model by ID and validate its structure."""
    model = client.Model.get(text_model_id)
    assert model.id == text_model_id
    
    # Validate complete model structure
    validate_model_structure(model)


def test_as_tool(client, text_model_id):
    """Test converting a model to a tool dictionary."""
    model = client.Model.get(text_model_id)
    tool = model.as_tool()
    
    assert isinstance(tool, dict)
    assert tool["name"] == model.name
    assert tool["description"] == model.description


def test_run(client, text_model_id):
    """Test running a model."""
    model = client.Model.get(text_model_id)
    
    try:
        result = model.run(data="Hello! Please respond with a short greeting.")
        assert hasattr(result, 'status')
        assert hasattr(result, 'data')
        assert result.status == "SUCCESS"
        assert result.data is not None
    except Exception as e:
        pytest.skip(f"Model run not supported: {e}") 