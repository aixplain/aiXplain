from typing import Union, List, Callable, TYPE_CHECKING
from typing_extensions import Unpack, NotRequired

from .resource import (
    BaseListParams,
    BaseResource,
    ListResourceMixin,
    GetResourceMixin,
    BareGetParams,
    Page,
)
from .enums import Function, Supplier, Language

if TYPE_CHECKING:
    from aixplain.modules.model.utility_model import UtilityModelInput


class ModelListParams(BaseListParams):
    """Parameters for listing models.

    Attributes:
        function: Function: The function of the model.
        suppliers: Union[Supplier, List[Supplier]: The suppliers of the model.
        source_languages: Union[Language, List[Language]: The source languages of the model.
        target_languages: Union[Language, List[Language]: The target languages of the model.
        is_finetunable: bool: Whether the model is finetunable.
    """

    function: NotRequired[Function]
    suppliers: NotRequired[Union[Supplier, List[Supplier]]]
    source_languages: NotRequired[Union[Language, List[Language]]]
    target_languages: NotRequired[Union[Language, List[Language]]]
    is_finetunable: NotRequired[bool]


class Model(
    BaseResource,
    ListResourceMixin[ModelListParams, "Model"],
    GetResourceMixin[BareGetParams, "Model"],
):
    """Resource for models."""

    RESOURCE_PATH = "sdk/models"

    @classmethod
    def list(cls, **kwargs: Unpack[ModelListParams]) -> Page["Model"]:
        from aixplain.factories import ModelFactory

        kwargs.setdefault("page_number", cls.PAGINATE_DEFAULT_PAGE_NUMBER)
        kwargs.setdefault("page_size", cls.PAGINATE_DEFAULT_PAGE_SIZE)

        return ModelFactory.list(**kwargs)

    @classmethod
    def get(cls, id: str, **kwargs: Unpack[BareGetParams]) -> "Model":
        from aixplain.factories import ModelFactory

        return ModelFactory.get(model_id=id)

    @classmethod
    def create_utility_model(
        cls,
        name: str,
        code: Union[str, Callable],
        inputs: List["UtilityModelInput"] = [],
        description: str = None,
        output_examples: str = "",
        api_key: str = None,
    ) -> "Model":
        from aixplain.factories import ModelFactory

        return Model(ModelFactory.create_utility_model(name, code, inputs, description, output_examples, api_key))

    @classmethod
    def list_host_machines(cls, api_key: str = None) -> List[str]:
        from aixplain.factories import ModelFactory

        return ModelFactory.list_host_machines(api_key)

    @classmethod
    def list_gpus(cls, api_key: str = None) -> List[str]:
        from aixplain.factories import ModelFactory

        return ModelFactory.list_gpus(api_key)

    @classmethod
    def list_functions(cls, verbose: bool = False, api_key: str = None) -> List[str]:
        from aixplain.factories import ModelFactory

        return ModelFactory.list_functions(verbose=verbose, api_key=api_key)

    @classmethod
    def create_asset_repo(
        cls,
        name: str,
        description: str,
        function: str,
        source_language: str,
        input_modality: str,
        output_modality: str,
        documentation_url: str = "",
        api_key: str = None,
    ) -> dict:
        from aixplain.factories import ModelFactory

        return ModelFactory.create_asset_repo(
            name,
            description,
            function,
            source_language,
            input_modality,
            output_modality,
            documentation_url,
            api_key,
        )

    @classmethod
    def asset_repo_login(cls, api_key: str = None) -> dict:
        from aixplain.factories import ModelFactory

        return ModelFactory.asset_repo_login(api_key=api_key)

    @classmethod
    def onboard_model(
        cls,
        model_id: str,
        image_tag: str,
        image_hash: str,
        host_machine: str = "",
        api_key: str = None,
    ) -> dict:
        from aixplain.factories import ModelFactory

        return ModelFactory.onboard_model(model_id, image_tag, image_hash, host_machine=host_machine, api_key=api_key)

    @classmethod
    def deploy_hugging_face_model(
        cls,
        name: str,
        hf_repo_id: str,
        revision: str = "",
        hf_token: str = "",
        api_key: str = None,
    ) -> dict:
        from aixplain.factories import ModelFactory

        return ModelFactory.deploy_hugging_face_model(
            name,
            hf_repo_id,
            revision=revision,
            hf_token=hf_token,
            api_key=api_key,
        )

    @classmethod
    def get_huggingface_model_status(cls, model_id: str, api_key: str = None) -> dict:
        from aixplain.factories import ModelFactory

        return ModelFactory.get_huggingface_model_status(model_id, api_key=api_key)
