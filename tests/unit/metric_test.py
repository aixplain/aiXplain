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

from dotenv import load_dotenv
import requests_mock

load_dotenv()
from aixplain.modules import Metric
from aixplain.factories import MetricFactory
from aixplain.enums import Supplier
from urllib.parse import urljoin

import pytest


def test_metric_factory_get():
    metric_id = "1"
    url = urljoin(MetricFactory.backend_url, f"sdk/metrics/{metric_id}")
    json_response = {
        "id": "1",
        "name": "rouge",
        "supplier": "aixplain",
        "referenceRequired": True,
        "sourceRequired": True,
        "normalizedPrice": 0.0,
        "function": "text_generation",
    }
    with requests_mock.Mocker() as m:
        m.get(url, json=json_response)
        metric = MetricFactory.get(metric_id)
        assert metric.id == metric_id
        assert metric.name == "rouge"
        assert metric.supplier == Supplier.AIXPLAIN
        assert metric.cost == 0.0
        assert metric.function == "text_generation"
        assert metric.is_reference_required is True
        assert metric.is_source_required is True


def test_metric_factory_get_exception():
    metric_id = "1"
    url = urljoin(MetricFactory.backend_url, f"sdk/metrics/{metric_id}")
    with requests_mock.Mocker() as m:
        m.get(url, status_code=404)
        with pytest.raises(Exception) as e:
            MetricFactory.get(metric_id)
            expected_message = "Status code: 404. Metric Creation: Unspecified error."
            assert str(e) == expected_message


def test_metric_factory_list():
    url = urljoin(MetricFactory.backend_url, "sdk/metrics")
    json_response = {
        "results": [
            {
                "id": "1",
                "name": "rouge",
                "supplier": "aixplain",
                "referenceRequired": True,
                "sourceRequired": True,
                "normalizedPrice": 0.0,
                "function": "text_generation",
            }
        ]
    }
    with requests_mock.Mocker() as m:
        m.get(url, json=json_response)
        metrics = MetricFactory.list()
        returned_keys = ["results", "page_total", "total", "page_number"]
        assert all(key in metrics for key in returned_keys)
        results = metrics["results"]
        assert len(results) == 1
        metric = results[0]
        assert metric.id == "1"
        assert metric.name == "rouge"
        assert metric.supplier == Supplier.AIXPLAIN
        assert metric.cost == 0.0
        assert metric.function == "text_generation"
        assert metric.is_reference_required is True
        assert metric.is_source_required is True


def test_metric_factory_list_exception():
    url = urljoin(MetricFactory.backend_url, "sdk/metrics")
    with requests_mock.Mocker() as m:
        m.get(url, status_code=404)
        results = MetricFactory.list()
        assert len(results) == 0


def test_metric_constructor():
    metric = Metric("1", "rouge", "aixplain", True, True, 0.0, "text_generation")
    assert metric.id == "1"
    assert metric.name == "rouge"
    assert metric.supplier == Supplier.AIXPLAIN
    assert metric.cost == 0.0
    assert metric.function == "text_generation"
    assert metric.is_reference_required is True
    assert metric.is_source_required is True
    assert metric.version == "1.0"


def test_metric_add_normalization_options():
    metric = Metric("1", "rouge", "aixplain", True, True, 0.0, "text_generation")
    assert metric.normalization_options == []
    metric.add_normalization_options(["option1", "option2"])
    assert metric.normalization_options == [["option1", "option2"]]


def test_metric_run(mocker):
    metric = Metric("1", "rouge", "aixplain", True, True, 0.0, "text_generation")
    model = mocker.MagicMock()
    model.run.return_value = "result"
    model_mocker = mocker.patch("aixplain.factories.model_factory.ModelFactory.get", return_value=model)
    response = metric.run("hypothesis", "source", "reference")
    assert response == "result"
    model_mocker.assert_called_with("1")
    model.run.assert_called_once()
    model.run.assert_called_with(
        {
            "function": "text_generation",
            "supplier": Supplier.AIXPLAIN,
            "version": "rouge",
            "hypotheses": ["hypothesis"],
            "sources": ["source"],
            "references": [["reference"]],
        }
    )
