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

import pytest

from aixplain.factories import ModelFactory, IntegrationFactory
from aixplain.modules import Model
from aixplain.modules.model.integration import Integration


def test_get_model_by_name():
    """Test getting a model by name returns the correct model instance."""
    model_name = "GPT-4o Mini"
    model = ModelFactory.get(name=model_name)

    assert isinstance(model, Model)
    assert model.name == model_name
    assert model.id is not None


def test_get_model_by_name_matches_get_by_id():
    """Test that getting a model by name returns the same model as getting by ID."""
    model_name = "GPT-4o Mini"

    # Get model by name
    model_by_name = ModelFactory.get(name=model_name)

    # Get the same model by ID
    model_by_id = ModelFactory.get(model_id=model_by_name.id)

    # Both should return the same model
    assert model_by_name.id == model_by_id.id
    assert model_by_name.name == model_by_id.name


def test_get_model_by_name_not_found():
    """Test that getting a model with a non-existent name raises an exception."""
    nonexistent_name = "This Model Does Not Exist 12345"

    with pytest.raises(Exception) as excinfo:
        ModelFactory.get(name=nonexistent_name)

    assert "Model GET by Name Error" in str(excinfo.value) or "404" in str(excinfo.value)


def test_integration_factory_get_by_name():
    """Test getting an Integration model by name using IntegrationFactory."""
    # Get a list of integrations to find a valid name
    integrations_result = IntegrationFactory.list(page_size=1)
    integrations = integrations_result.get("results", [])

    if len(integrations) == 0:
        pytest.skip("No integrations available for testing")

    integration_name = integrations[0].name

    # Get the integration by name
    integration = IntegrationFactory.get(name=integration_name)

    assert isinstance(integration, Integration)
    assert integration.name == integration_name
    assert integration.id is not None


def test_integration_factory_get_by_name_not_found():
    """Test that IntegrationFactory.get raises an error for non-existent integration names."""
    nonexistent_name = "This Integration Does Not Exist 12345"

    with pytest.raises(Exception) as excinfo:
        IntegrationFactory.get(name=nonexistent_name)

    assert "Integration GET by Name Error" in str(excinfo.value)
