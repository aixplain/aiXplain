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
from aixplain import aixplain_v2 as v2

INPUTS_PATH = Path(r"tests/functional/general_assets/data/asset_run_test_data.json")


@pytest.fixture
def inputs():
    with open(INPUTS_PATH) as f:
        return json.load(f)


@pytest.mark.parametrize("ModelFactory", [ModelFactory, v2.Model])
def test_list_models(ModelFactory):
    models = ModelFactory.list(function=Function.TRANSLATION)
    assert models["page_total"] == len(models["results"])


@pytest.mark.parametrize("DatasetFactory", [DatasetFactory, v2.Dataset])
def test_list_datasets(DatasetFactory):
    datasets = DatasetFactory.list()
    assert datasets["page_total"] == len(datasets["results"])


@pytest.mark.parametrize("MetricFactory", [MetricFactory, v2.Metric])
def test_list_metrics(MetricFactory):
    metrics = MetricFactory.list()
    assert metrics["page_total"] == len(metrics["results"])


@pytest.mark.parametrize("PipelineFactory", [PipelineFactory, v2.Pipeline])
def test_run_pipeline(inputs, PipelineFactory):
    asset_details = inputs["pipeline"]
    pipeline = PipelineFactory.list(query=asset_details["name"])["results"][0]
    payload = asset_details["data"]
    output = pipeline.run(payload)
    assert output["completed"] and output["status"] == "SUCCESS"


@pytest.mark.parametrize("MetricFactory", [MetricFactory, v2.Metric])
def test_run_metric(inputs, MetricFactory):
    asset_details = inputs["metric"]
    metric = MetricFactory.get(asset_details["id"])
    payload = asset_details["data"]
    output = metric.run(**payload)
    assert output["completed"] and output["status"] == "SUCCESS"


@pytest.mark.parametrize("ModelFactory", [ModelFactory, v2.Model])
def test_run_model(inputs, ModelFactory):
    asset_details = inputs["model"]
    model = ModelFactory.get(asset_details["id"])
    payload = asset_details["data"]
    output = model.run(payload)
    assert output["completed"] and output["status"] == "SUCCESS"


@pytest.mark.parametrize("ModelFactory", [ModelFactory, v2.Model])
def test_model_function(ModelFactory):
    desired_function = Function.TRANSLATION
    models = ModelFactory.list(function=desired_function)["results"]
    for model in models:
        assert model.function == desired_function


@pytest.mark.parametrize("ModelFactory", [ModelFactory, v2.Model])
def test_model_supplier(ModelFactory):
    desired_suppliers = [Supplier.GOOGLE]
    models = ModelFactory.list(suppliers=desired_suppliers, function=Function.TRANSLATION)["results"]
    for model in models:
        assert model.supplier.value in [desired_supplier.value for desired_supplier in desired_suppliers]


@pytest.mark.parametrize(
    "model_ids,model_names",
    [
        (("674728f51ed8e18fd8a1383f", "669a63646eb56306647e1091"), ("Yi-Large", "GPT-4o Mini")),
    ],
)
@pytest.mark.parametrize("ModelFactory", [ModelFactory, v2.Model])
def test_model_ids(model_ids, model_names, ModelFactory):
    models = ModelFactory.list(model_ids=model_ids)["results"]
    assert len(models) == 2
    assert sorted([model.id for model in models]) == sorted(model_ids)
    assert sorted([model.name for model in models]) == sorted(model_names)


@pytest.mark.parametrize("ModelFactory", [ModelFactory, v2.Model])
def test_model_sort(ModelFactory):
    function = Function.TRANSLATION
    src_language = Language.Portuguese
    trg_language = Language.English

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


@pytest.mark.parametrize("ModelFactory", [ModelFactory, v2.Model])
def test_model_ownership(ModelFactory):
    models = ModelFactory.list(ownership=OwnershipType.SUBSCRIBED, function=Function.TRANSLATION)["results"]
    for model in models:
        assert model.is_subscribed is True


@pytest.mark.parametrize("ModelFactory", [ModelFactory, v2.Model])
def test_model_query(ModelFactory):
    query = "Mongo"
    models = ModelFactory.list(query=query, function=Function.TRANSLATION)["results"]
    for model in models:
        assert query in model.name


@pytest.mark.parametrize("ModelFactory", [ModelFactory, v2.Model])
def test_model_deletion(ModelFactory):
    """Test that a model cannot be deleted."""
    model = ModelFactory.get("640b517694bf816d35a59125")
    with pytest.raises(Exception):
        model.delete()


@pytest.mark.parametrize("ModelFactory", [ModelFactory, v2.Model])
def test_llm_instantiation(ModelFactory):
    """Test that the LLM model is correctly instantiated."""
    models = ModelFactory.list(function=Function.TEXT_GENERATION)["results"]
    assert isinstance(models[0], LLM)


@pytest.mark.parametrize("ModelFactory", [ModelFactory, v2.Model])
def test_model_io(ModelFactory):
    model_id = "64aee5824d34b1221e70ac07"
    model = ModelFactory.get(model_id)

    expected_input = {
        "text": {
            "name": "Text Prompt",
            "code": "text",
            "required": True,
            "isFixed": False,
            "dataType": "text",
            "dataSubType": "text",
            "multipleValues": False,
            "defaultValues": [],
        }
    }
    expected_output = {
        "data": {
            "name": "Generated Image",
            "code": "data",
            "defaultValue": [],
            "dataType": "image",
        }
    }

    assert model.input_params == expected_input
    assert model.output_params == expected_output
