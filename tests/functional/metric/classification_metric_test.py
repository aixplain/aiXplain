import pytest
from dotenv import load_dotenv
from aixplain.factories import MetricFactory
import json
load_dotenv()


INPUT_FILE_PATH = "data/classification_metrics_input.json"
OUTPUT_FILE_PATH = "data/classification_metrics_output.json"


def read_data(data_path):
    return json.load(open(data_path, "r"))


INPUTS = read_data(INPUT_FILE_PATH)
OUTPUTS = read_data(OUTPUT_FILE_PATH)
METRIC_IDs = INPUTS.keys()


@pytest.mark.parametrize("metric_id", METRIC_IDs)
def test_metric_run(metric_id):
    metric = MetricFactory.get(metric_id)
    inp = INPUTS[metric_id]
    expected_output = OUTPUTS[metric_id]
    hyp, ref = inp["hypotheses"], inp["references"]
    actual_output = metric.run(**{"hypothesis": hyp, "reference": ref})
    actual_output = actual_output["details"]
    for key in expected_output:
        assert expected_output[key] == actual_output[key]
