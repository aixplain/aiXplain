"""Argument-validation tests for `IndexFactory.create`.

Moved out of `tests/functional/` by BUG-947, where it occupied a CI leg running
against the production tenant. Every create is inside `pytest.raises` and
`IndexFactory.create` asserts on its own arguments before issuing any request,
so the validation itself needs neither a credential nor a network.

One argument does: building an `AirParams` runs a pydantic field validator that
calls ``ModelFactory.get(embedding_model)`` to check the model is a text
embedding model, and that is a live GET. It happens while evaluating the
argument, so the resulting error is caught by `pytest.raises` and surfaces as a
mismatched message rather than as a connection error -- which is how a test that
silently required a backend could look green on a developer's laptop and fail
the credential-free `unit-coverage` job. The lookup is stubbed out here instead;
it is not what these tests are about.
"""

import pytest
from aixplain.enums import EmbeddingModel, Function
from aixplain.factories.index_factory import IndexFactory
from aixplain.factories.index_factory import utils as index_factory_utils


@pytest.fixture
def stub_embedding_model_lookup(mocker):
    """Make the `AirParams` embedding-model validator resolve without a backend."""
    return mocker.patch.object(
        index_factory_utils.ModelFactory,
        "get",
        return_value=mocker.Mock(function=Function.TEXT_EMBEDDING),
    )


def test_index_factory_create_rejects_params_alongside_legacy_arguments(stub_embedding_model_lookup):
    from aixplain.factories.index_factory.utils import AirParams

    params = AirParams(name="test", description="test", embedding_model=EmbeddingModel.OPENAI_ADA002)

    with pytest.raises(Exception) as e:
        IndexFactory.create(
            name="test",
            description="test",
            embedding_model=EmbeddingModel.OPENAI_ADA002,
            params=params,
        )
    assert (
        str(e.value)
        == "Index Factory Exception: name, description, and embedding_model must not be provided when params is provided"
    )


@pytest.mark.parametrize(
    "kwargs",
    [
        {"description": "test"},
        {"name": "test"},
        {"name": "test", "description": "test", "embedding_model": None},
    ],
    ids=["description-only", "name-only", "no-embedding-model"],
)
def test_index_factory_create_requires_every_legacy_argument(kwargs):
    """No `params`, so nothing resolves a model: these need no backend at all."""
    with pytest.raises(Exception) as e:
        IndexFactory.create(**kwargs)
    assert (
        str(e.value)
        == "Index Factory Exception: name, description, and embedding_model must be provided when params is not"
    )
