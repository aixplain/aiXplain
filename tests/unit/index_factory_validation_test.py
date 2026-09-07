"""Argument-validation tests for `IndexFactory.create`.

Moved out of `tests/functional/` by BUG-947: every create here is inside
`pytest.raises` and the SDK raises while validating its arguments, before any
HTTP call is made, so this needs neither a credential nor a network -- and used
to occupy a CI leg running against the production tenant.
"""

import pytest
from aixplain.enums import EmbeddingModel
from aixplain.factories.index_factory import IndexFactory


def test_index_factory_create_failure():
    from aixplain.factories.index_factory.utils import AirParams

    with pytest.raises(Exception) as e:
        IndexFactory.create(
            name="test",
            description="test",
            embedding_model=EmbeddingModel.OPENAI_ADA002,
            params=AirParams(name="test", description="test", embedding_model=EmbeddingModel.OPENAI_ADA002),
        )
    assert (
        str(e.value)
        == "Index Factory Exception: name, description, and embedding_model must not be provided when params is provided"
    )

    with pytest.raises(Exception) as e:
        IndexFactory.create(description="test")
    assert (
        str(e.value)
        == "Index Factory Exception: name, description, and embedding_model must be provided when params is not"
    )

    with pytest.raises(Exception) as e:
        IndexFactory.create(name="test")
    assert (
        str(e.value)
        == "Index Factory Exception: name, description, and embedding_model must be provided when params is not"
    )

    with pytest.raises(Exception) as e:
        IndexFactory.create(name="test", description="test", embedding_model=None)
    assert (
        str(e.value)
        == "Index Factory Exception: name, description, and embedding_model must be provided when params is not"
    )
