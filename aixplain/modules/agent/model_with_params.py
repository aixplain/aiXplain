"""A generic class that wraps a model with extra parameters.

This is an abstract base class that must be extended by specific model wrappers.

Example usage:

class MyModel(ModelWithParams):
    model_id: Text = "my_model"
    extra_param: int = 10

    @field_validator("extra_param")
    def validate_extra_param(cls, v: int) -> int:
        if v < 0:
            raise ValueError("Extra parameter must be positive")
        return v
"""

from abc import ABC
from typing import Text

from pydantic import BaseModel, ConfigDict, field_validator
from pydantic.alias_generators import to_camel


class ModelWithParams(BaseModel, ABC):
    """A generic class that wraps a model with extra parameters.

    The extra parameters are not part of the model's input/output parameters.
    This is an abstract base class that must be extended by specific model wrappers.

    Attributes:
        model_id: The ID of the model to wrap.
    """

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    model_id: Text

    @field_validator("model_id")
    def validate_model_id(cls, v: Text) -> Text:
        """Validate the model_id field.

        This validator ensures that the model_id is not empty or whitespace-only.

        Args:
            cls: The class (automatically provided by pydantic).
            v (Text): The value to validate.

        Returns:
            Text: The validated model ID.

        Raises:
            ValueError: If the model ID is empty or contains only whitespace.
        """
        if not v or not v.strip():
            raise ValueError("Model ID is required")
        return v

    def __new__(cls, *args, **kwargs):
        """Create a new instance of a ModelWithParams subclass.

        This method prevents direct instantiation of the abstract base class while
        allowing subclasses to be instantiated normally.

        Args:
            cls: The class being instantiated.
            *args: Positional arguments for instance creation.
            **kwargs: Keyword arguments for instance creation.

        Returns:
            ModelWithParams: A new instance of a ModelWithParams subclass.

        Raises:
            TypeError: If attempting to instantiate ModelWithParams directly.
        """
        if cls is ModelWithParams:
            raise TypeError("ModelWithParams is an abstract base class and cannot be instantiated directly")
        return super().__new__(cls)
