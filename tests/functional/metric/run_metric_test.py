import pytest
from dotenv import load_dotenv
from aixplain.factories import MetricFactory
import json
import random
load_dotenv()


TEXT_GENERATION_INPUT_FILE_PATH = "tests/functional/metric/data/text_generation_inputs.json"
TEXT_GENERATION_OUTPUT_FILE_PATH = "tests/functional/metric/data/text_generation_outputs.json"


def fetch_metric_parameters(metric_type: str, number_of_metrics: int, number_of_tests: int):
    """
    Fetch the metric parameters from the input file

    Args:
        metric_type (str): The type of metric to fetch. Valid values are "text_generation" and "classification"
        number_of_metrics (int): The number of metrics to fetch. Use -1 for all
        number_of_tests (int): The number of tests to fetch. Use -1 for all
    """
    if metric_type == "text_generation":
        input_file_path = TEXT_GENERATION_INPUT_FILE_PATH
        output_file_path = TEXT_GENERATION_OUTPUT_FILE_PATH
    else:
        raise ValueError(f"Invalid metric type: {metric_type}")
    
    with open(input_file_path, 'r') as file:
        input_data = json.load(file)

    with open(output_file_path, 'r') as file:
        output_data = json.load(file)

    sampled_metrics = dict(random.sample(output_data.items(), min(number_of_metrics, len(output_data)) if number_of_metrics > 0 else len(output_data)))
    for metric_name, metric_info in sampled_metrics.items():
        metric_id = metric_info['model_id']
        all_expected_outputs = metric_info['expected_outputs']
        sampled_tests = dict(random.sample(all_expected_outputs.items(), min(number_of_tests, len(all_expected_outputs)) if number_of_tests > 0 else len(all_expected_outputs)))
        for test_name, expected_outputs in sampled_tests.items():
            yield metric_name, metric_id, expected_outputs, input_data[test_name]




@pytest.mark.parametrize("metric_name, metric_id, expected_outputs, input_data", fetch_metric_parameters("text_generation", -1, -1))
def test_all_text_generation_metrics(metric_name, metric_id, expected_outputs, input_data):
    metric = MetricFactory.get(metric_id)
    predicted_outputs = metric.run(**input_data)["details"]
    for key in expected_outputs:
        assert expected_outputs[key] == predicted_outputs[key]
