import requests

from typing import Dict, Any, Type, Optional, List, Callable
from urllib.parse import urlencode

from aixplain.env import client as env_client
from aixplain.client import AixplainClient


class BaseAsset:
    """
    Base class for representing assets. Subclasses should define the attribute
    'asset_path' for specific functionality.

    Attributes:
        asset_path (str): The path to the asset. Subclasses must define this
                          attribute.
        client (AixplainClient): The client used to interact with the asset.
    """

    # Subclasses should define the attribute 'asset_path'
    asset_path = None

    client: AixplainClient = env_client

    def __init__(self, obj: Dict[str, Any]):
        """
        Initialize a BaseAsset instance.

        :param obj: Dictionary containing the asset's attributes.
        """
        self._obj = obj

    def __getattr__(self, key: str) -> Any:
        """
        Return the value corresponding to the key from the wrapped dictionary
        if found, otherwise raise an AttributeError.

        :param key: Attribute name to retrieve from the asset.
        :return: Value corresponding to the specified key.
        :raises AttributeError: If the key is not found in the wrapped
                                dictionary.
        """
        if key in self._obj:
            return self._obj[key]
        raise AttributeError(f"Object has no attribute '{key}'")

    def _action(self, method: Optional[str] = None,
                action_paths: List[str] = None, **kwargs) -> requests.Response:
        """
        Internal method to perform actions on the asset.

        :param method: HTTP method to use (default is 'GET').
        :param action_paths: Optional list of action paths to append to the
                             URL.
        :param kwargs: Additional keyword arguments to pass to the request.
        :return: Response from the client's request as requests.Response
        :raises ValueError: If 'asset_path' is not defined by the subclass or
                            'id' attribute is missing.
        """
        if not self.asset_path:
            raise ValueError(
                "Subclasses of 'BaseAsset' must specify 'asset_path'")

        if not self.id:
            raise ValueError("Action call requires an 'id' attribute")

        method = method or 'GET'
        path = f'sdk/{self.asset_path}/{self.id}'
        if action_paths:
            path += '/' + '/'.join(['', *action_paths])

        return self.client.request(method, path, **kwargs)


class GetAssetMixin:

    @classmethod
    def get(cls: Type['BaseAsset'], asset_id: str, **kwargs) -> 'BaseAsset':
        """
        Retrieve an Asset instance by its ID.

        :param asset_id: ID of the asset.
        :param kwargs: Additional keyword arguments to pass to the request.
        :return: Instance of the BaseAsset class.
        :raises ValueError: If 'asset_path' is not defined by the subclass.
        """
        if cls.asset_path is None:
            raise ValueError(
                "Subclasses of 'BaseAsset' must specify 'asset_path'")

        path = f'sdk/{cls.asset_path}/{asset_id}'
        response = cls.client.get(path, **kwargs)
        obj = response.json()
        return cls(obj)


class ListAssetMixin:

    @classmethod
    def _construct_page_path(cls: Type['BaseAsset'], page_number: int,
                             filters: Optional[Dict[str, Any]] = None,
                             subpaths: Optional[List[str]] = None, **kwargs) -> str:
        """
        Construct a URL to list assets.

        :param page_number: Page number for pagination.
        :param filters: Optional dictionary of additional filter parameters.
        :param subpaths: Optional list of subpaths to append to the URL.
        :return: Constructed URL.
        """
        path = f'sdk/{cls.asset_path}'
        if subpaths:
            path += '/'.join(['', *subpaths])

        params = {'pageNumber': page_number}

        if filters:
            params.update(filters)

        query = urlencode(params)

        return f'{path}?{query}'

    @classmethod
    def _page(cls: Type['BaseAsset'], path: str,
              **kwargs) -> List['BaseAsset']:
        """
        Internal method to retrieve assets for a specific page.

        :param path: The URL of the page to retrieve assets from.
        :param kwargs: Additional keyword arguments to customize the request,
                       including 'page_number' and 'filters', if required.
        :return: List of BaseAsset instances for the specified page.
        """
        payload = cls.client.get(path, **kwargs)
        payload_json = payload.json()
        if 'items' in payload_json:
            key = 'items'
        else:
            key = 'results'
        return [cls(item) for item in payload_json[key]]

    @classmethod
    def page(cls: Type['BaseAsset'], page_number: int,
             filters: Optional[Dict[str, Any]] = None,
             subpaths: Optional[List[str]] = None,
             **kwargs) -> List['BaseAsset']:
        """
        List assets for a specific page with optional filtering.

        :param page_number: Page number for pagination.
        :param filters: Optional dictionary containing filters to apply to the
                        results.
        :param kwargs: Additional filter parameters.
        :return: List of BaseAsset instances for the specified page.
        """
        path = cls._construct_page_path(page_number, filters=filters, subpaths = subpaths)
        return cls._page(path=path, **kwargs)

    @classmethod
    def list(cls: Type['BaseAsset'],
             n: int = 1,
             filters: Optional[Dict[str, Any]] = None,
             page_fn: Optional[Callable[[int, Optional[Dict[str, Any]], Any],
                                        List['BaseAsset']]] = None,
             subpaths: Optional[List[str]] = None,
             **kwargs) -> List['BaseAsset']:
        """
        List assets across the first n pages with optional filtering.

        :param n: Optional number of pages to fetch (default is 1).
        :param filters: Optional dictionary containing filters to apply to the
                        results.
        :param page_fn: Optional custom function to replace the default page
                        method.
        :param kwargs: Additional filter parameters.
        :return: List of BaseAsset instances across n pages
        """
        assets = []
        page_fn = page_fn or cls.page
        for page_number in range(0, n):
            assets += page_fn(page_number, filters=filters, subpaths = subpaths, **kwargs)
        return assets
