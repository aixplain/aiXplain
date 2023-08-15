from typing import Dict, Any, Type, Optional, List, Callable

from aixplain.assets import BaseAsset, GetAssetMixin, ListAssetMixin


class Dataset(BaseAsset, GetAssetMixin, ListAssetMixin):
    """
    Represents a Dataset asset, extending functionality of BaseAsset with
    specific actions like fetching datasets associated with a team and
    downloading datasets.

    Attributes:
        asset_path (str): Specifies the path for the Dataset assets, set to
                          'datasets'.
    """

    asset_path = 'datasets'

    @classmethod
    def team_page(cls: Type['BaseAsset'], page_number: int,
                  filters: Optional[Dict[str, Any]] = None,
                  **kwargs) -> List['BaseAsset']:
        """
        Retrieves a list of datasets associated with the team for a specific
        page.

        :param page_number: Page number for pagination.
        :param filters: Optional dictionary containing filters to apply to the
                        results.
        :param kwargs: Additional filter parameters.
        :return: List of Dataset instances for the specified page.
        """
        path = cls._construct_page_path(page_number=page_number,
                                        filters=filters,
                                        subpaths=['team'],
                                        **kwargs)
        return cls._page(path=path, **kwargs)

    @classmethod
    def team_list(cls: Type['BaseAsset'],
                  n: int = 1,
                  filters: Optional[Dict[str, Any]] = None,
                  page_fn: Optional[Callable[[int, Optional[Dict[str, Any]],
                                             Any],
                                             List['BaseAsset']]] = None,
                  **kwargs) -> List['BaseAsset']:
        """
        Retrieves datasets associated with the team across the first n pages
        with optional filtering.

        :param n: Optional number of pages to fetch (default is 1).
        :param filters: Optional dictionary containing filters to apply to the
                        results.
        :param page_fn: Optional custom function to replace the default page
                        method, defaults to cls.team_page.
        :param kwargs: Additional filter parameters.
        :return: List of Dataset instances across n pages.
        """
        return cls.list(n=n, filters=filters, page_fn=cls.team_page, **kwargs)

    def download(self, **kwargs):
        """
        Initiates a download request for the dataset.

        :param kwargs: Additional keyword arguments to pass to the request.
        :return: Response from the client's request as requests.Response
        """
        return self._action(action_paths=['download'], **kwargs)
