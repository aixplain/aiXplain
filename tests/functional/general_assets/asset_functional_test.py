import json
from dotenv import load_dotenv

load_dotenv()
from aixplain.factories import (
    ModelFactory,
    DatasetFactory,
    MetricFactory,
    PipelineFactory,
)
from aixplain.modules import LLM
from pathlib import Path
from aixplain.enums import (
    Function,
    Language,
    OwnershipType,
    Supplier,
    SortBy,
    SortOrder,
)

import pytest

INPUTS_PATH = Path(r"tests/functional/general_assets/data/asset_run_test_data.json")


@pytest.fixture
def inputs():
    with open(INPUTS_PATH) as f:
        return json.load(f)


@pytest.mark.parametrize("ModelFactory", [ModelFactory])
def test_list_models(ModelFactory):
    models = ModelFactory.list(function=Function.TRANSLATION)
    assert models["page_total"] == len(models["results"])


@pytest.mark.parametrize("DatasetFactory", [DatasetFactory])
def test_list_datasets(DatasetFactory):
    datasets = DatasetFactory.list()
    assert datasets["page_total"] == len(datasets["results"])


@pytest.mark.parametrize("MetricFactory", [MetricFactory])
def test_list_metrics(MetricFactory):
    metrics = MetricFactory.list()
    assert metrics["page_total"] == len(metrics["results"])


@pytest.mark.parametrize("PipelineFactory", [PipelineFactory])
def test_run_pipeline(inputs, PipelineFactory):
    asset_details = inputs["pipeline"]
    pipeline = PipelineFactory.list(query=asset_details["name"])["results"][0]
    payload = asset_details["data"]
    output = pipeline.run(payload)
    assert output["completed"] and output["status"] == "SUCCESS"


@pytest.mark.parametrize("MetricFactory", [MetricFactory])
def test_run_metric(inputs, MetricFactory):
    asset_details = inputs["metric"]
    metric = MetricFactory.get(asset_details["id"])
    payload = asset_details["data"]
    output = metric.run(**payload)
    assert output["completed"] and output["status"] == "SUCCESS"


@pytest.mark.parametrize("ModelFactory", [ModelFactory])
def test_run_model(inputs, ModelFactory):
    asset_details = inputs["model"]
    model = ModelFactory.get(asset_details["id"])
    payload = asset_details["data"]
    output = model.run(payload)
    assert output["completed"] and output["status"] == "SUCCESS"


@pytest.mark.parametrize("ModelFactory", [ModelFactory])
def test_model_function(ModelFactory):
    desired_function = Function.TRANSLATION
    models = ModelFactory.list(function=desired_function)["results"]
    for model in models:
        assert model.function == desired_function


@pytest.mark.parametrize("ModelFactory", [ModelFactory])
def test_model_supplier(ModelFactory):
    desired_suppliers = [Supplier.GOOGLE]
    models = ModelFactory.list(suppliers=desired_suppliers, function=Function.TRANSLATION)["results"]
    # Check that we got some results
    assert len(models) > 0, "Should return models with Google supplier"
    # Verify ALL returned models match the supplier filter
    desired_supplier_values = [desired_supplier.value for desired_supplier in desired_suppliers]
    for model in models:
        # Compare supplier values (which are dicts with id, name, code)
        model_supplier_value = model.supplier.value if hasattr(model.supplier, "value") else model.supplier
        # Check if model supplier matches any desired supplier by comparing the 'id' field
        model_supplier_id = model_supplier_value.get("id") if isinstance(model_supplier_value, dict) else None
        desired_supplier_ids = [sv.get("id") for sv in desired_supplier_values if isinstance(sv, dict)]
        assert model_supplier_id in desired_supplier_ids, (
            f"Model {model.id} has supplier {model_supplier_value}, expected one of {desired_supplier_values}"
        )


@pytest.mark.parametrize(
    "model_ids,model_names",
    [
        (
            ("67be216bd8f6a65d6f74d5e9", "669a63646eb56306647e1091"),
            ("Anthropic Claude 3.7 Sonnet", "GPT-4o Mini"),
        ),
    ],
)
@pytest.mark.parametrize("ModelFactory", [ModelFactory])
def test_model_ids(model_ids, model_names, ModelFactory):
    models = ModelFactory.list(model_ids=model_ids)["results"]
    assert len(models) == 2
    assert sorted([model.id for model in models]) == sorted(model_ids)
    assert sorted([model.name for model in models]) == sorted(model_names)


@pytest.mark.parametrize("ModelFactory", [ModelFactory])
def test_model_sort(ModelFactory):
    function = Function.TRANSLATION
    src_language = Language.PORTUGUESE
    trg_language = Language.ENGLISH

    models = ModelFactory.list(
        function=function,
        source_languages=src_language,
        target_languages=trg_language,
        sort_by=SortBy.PRICE,
        sort_order=SortOrder.DESCENDING,
    )["results"]
    for idx in range(1, len(models)):
        prev_model = models[idx - 1]
        model = models[idx]

        prev_model_price = prev_model.cost["price"]
        model_price = model.cost["price"]
        assert prev_model_price >= model_price


@pytest.mark.parametrize("ModelFactory", [ModelFactory])
def test_model_ownership(ModelFactory):
    models = ModelFactory.list(ownership=OwnershipType.SUBSCRIBED, function=Function.TRANSLATION)["results"]
    for model in models:
        assert model.is_subscribed is True


@pytest.mark.parametrize("ModelFactory", [ModelFactory])
def test_model_query(ModelFactory):
    query = "Mongo"
    models = ModelFactory.list(query=query, function=Function.TRANSLATION)["results"]
    for model in models:
        assert query in model.name


@pytest.mark.parametrize("ModelFactory", [ModelFactory])
def test_model_deletion(ModelFactory):
    """Test that a model cannot be deleted."""
    model = ModelFactory.get("640b517694bf816d35a59125")
    with pytest.raises(Exception):
        model.delete()


@pytest.mark.parametrize("ModelFactory", [ModelFactory])
def test_llm_instantiation(ModelFactory):
    """Test that the LLM model is correctly instantiated."""
    models = ModelFactory.list(function=Function.TEXT_GENERATION)["results"]
    assert isinstance(models[0], LLM)


@pytest.mark.parametrize("ModelFactory", [ModelFactory])
def test_model_io(ModelFactory):
    model_id = "64aee5824d34b1221e70ac07"
    model = ModelFactory.get(model_id)

    # Verify input_params structure matches actual API response
    assert "text" in model.input_params, "Model should have 'text' input parameter"
    text_input = model.input_params["text"]
    assert text_input["code"] == "text"
    assert text_input["dataType"] == "text"
    assert text_input["required"] is True
    assert text_input["multipleValues"] is False
    assert text_input["defaultValues"] == []
    assert text_input["isFixed"] is False

    # Verify output_params structure matches actual API response
    assert "data" in model.output_params, "Model should have 'data' output parameter"
    data_output = model.output_params["data"]
    assert data_output["code"] == "data"
    assert data_output["dataType"] == "image"
    assert "defaultValue" in data_output or "defaultValues" in data_output
