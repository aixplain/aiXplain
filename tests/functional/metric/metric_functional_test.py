__author__ = "lucaspavanelli"
"""
Copyright 2022 The aiXplain SDK authors

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

     http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""
import json
from dotenv import load_dotenv
import pytest

load_dotenv()
from aixplain.factories import MetricFactory

RUN_FILE = "tests/functional/metric/data/metric_test_end2end.json"


def read_data(data_path):
    return json.load(open(data_path, "r"))


@pytest.fixture(scope="module", params=read_data(RUN_FILE))
def run_input_map(request):
    return request.param


def test_end2end(run_input_map):
    metric_id = run_input_map["id"]
    hypothesis = run_input_map["hypothesis"]
    reference = run_input_map["reference"]
    metric = MetricFactory.get(metric_id)
    result = metric.run(hypothesis=hypothesis, reference=reference)
    assert result is not None
    assert result["status"] == "SUCCESS"
    assert result["completed"] is True
    assert "details" in result
    assert "data" in result
    assert len(result["data"]) == 1
    assert result["data"][0]["score"] == run_input_map["score"]


def test_list_metric():
    metric_list = MetricFactory.list()["results"]
    assert len(metric_list) > 0


# TODO test the following list: rouge, overlap f1, wder, der, wer, precision, recall, f1 and accuracy
