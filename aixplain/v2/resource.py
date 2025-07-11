import requests
from typing import (
    List,
    TypeVar,
    Any,
    Union,
    TYPE_CHECKING,
)

# Re-export essential classes for backward compatibility
from .mixins import (  # noqa: F401
    # Parameter classes
    BaseApiKeyParams,
    BaseListParams,
    BaseGetParams,
    BaseCreateParams,
    BaseDeleteParams,
    BaseRunParams,
    BareListParams,
    BareGetParams,
    BareCreateParams,
    BareDeleteParams,
    BareRunParams,
    # Core classes
    Page,
    # Mixins
    ListResourceMixin,
    GetResourceMixin,
    CreateResourceMixin,
    DeleteResourceMixin,
    RunnableMixin,
    # Response classes
    BaseRunnableResponse,
    RunnableResponse,
)

if TYPE_CHECKING:
    from .core import Aixplain


class BaseResource:
    """Base class for all resources.

    Attributes:
        context: Aixplain: The Aixplain instance.
        RESOURCE_PATH: str: The resource path.
    """

    _obj: Union[dict, Any]
    context: "Aixplain"
    RESOURCE_PATH: str

    def __init__(self, obj: Union[dict, Any]):
        """
        Initialize a BaseResource instance.

        Args:
            obj: dict: Dictionary containing the resource's attributes.
        """
        self._obj = obj

    @classmethod
    def _get_api_key(cls, kwargs: dict) -> str:
        """
        Get API key from kwargs or context, with fallback to config for
        backwards compatibility.
        
        Args:
            kwargs: dict: Keyword arguments passed to the method.
            
        Returns:
            str: API key from kwargs, context, or config.TEAM_API_KEY as
                 fallback.
        """
        api_key = kwargs.get("api_key") or getattr(cls.context, "api_key", None)
        
        if api_key is None:
            import aixplain.utils.config as config
            api_key = config.TEAM_API_KEY
            
        return api_key

    def __getattr__(self, key: str) -> Any:
        """
        Return the value corresponding to the key from the wrapped dictionary
        if found, otherwise raise an AttributeError.

        Args:
            key: str: Attribute name to retrieve from the resource.

        Returns:
            Any: Value corresponding to the specified key.

        Raises:
            AttributeError: If the key is not found in the wrapped
                                dictionary.
        """
        if isinstance(self._obj, dict):
            if key in self._obj:
                return self._obj[key]
            raise AttributeError(f"Object has no attribute '{key}'")
        return getattr(self._obj, key)

    def save(self):
        """Save the resource.

        If the resource has an ID, it will be updated, otherwise it will be
        created.
        """
        if hasattr(self, "id") and self.id:
            self._action("put", [self.id], **self._obj)
        else:
            self._action("post", **self._obj)

    def _action(
        self, method: str = None, action_paths: List[str] = None, **kwargs
    ) -> requests.Response:
        """
        Internal method to perform actions on the resource.

        Args:
            method: str, optional: HTTP method to use (default is 'GET').
            action_paths: List[str], optional: Optional list of action paths
                to append to the URL.
            kwargs: dict: Additional keyword arguments to pass to the request.

        Returns:
            requests.Response: Response from the client's request as
                requests.Response

        Raises:
            ValueError: If 'RESOURCE_PATH' is not defined by the subclass or
                'id' attribute is missing.
        """

        assert getattr(
            self, "RESOURCE_PATH"
        ), "Subclasses of 'BaseResource' must specify 'RESOURCE_PATH'"

        if not self.id:
            raise ValueError("Action call requires an 'id' attribute")

        method = method or "GET"
        path = f"sdk/{self.RESOURCE_PATH}/{self.id}"
        if action_paths:
            path += "/".join(["", *action_paths])

        return self.context.client.request(method, path, **kwargs)

    def __repr__(self) -> str:
        if hasattr(self, "name"):
            return f"{self.__class__.__name__}(id={self.id}, name={self.name})"
        return f"{self.__class__.__name__}(id={self.id})"


# Re-export the resource type variable for backward compatibility
R = TypeVar("R", bound=BaseResource)
