import pytest
from typing import Any, Callable

from dotenv import load_dotenv

# Load environment variables once for all tests
load_dotenv(override=True)

SDK_VERSION_ARG = "--sdk_version"
SDK_VERSION_PARAM_ARG = "--sdk_version_param"
PIPELINE_VERSION_ARG = "--pipeline_version"

SDK_VERSION_V1 = "v1"
SDK_VERSION_V2 = "v2"
SDK_VERSIONS = [SDK_VERSION_V1, SDK_VERSION_V2]

PIPELINE_VERSION_2_0 = "2.0"
PIPELINE_VERSION_3_0 = "3.0"
PIPELINE_VERSIONS = [PIPELINE_VERSION_2_0, PIPELINE_VERSION_3_0]


def pytest_addoption(parser: pytest.Parser):
    # Here we're adding the options for the pipeline version and the sdk version
    parser.addoption(f"{PIPELINE_VERSION_ARG}", action="store", help="pipeline version")
    parser.addoption(f"{SDK_VERSION_ARG}", action="store", help="sdk version")
    parser.addoption(f"{SDK_VERSION_PARAM_ARG}", action="store", help="sdk version parameter")


def filter_items(items: list, param_name: str, predicate: Callable):
    """Filter the items based on the parameter name and the predicate.

    Args:
        items (list): The list of items to filter.
        param_name (str): The parameter name to filter by.
        predicate (callable): The predicate to filter by.
    """
    items[:] = [
        item
        for item in items
        if hasattr(item, "callspec")
        and param_name in item.callspec.params
        and predicate(item.callspec.params[param_name])
    ]


def filter_pipeline_version(items: list, pipeline_version: str):
    """Filter the items based on the pipeline version.

    Args:
        items (list): The list of items to filter.
        pipeline_version (str): The pipeline version to filter by.

    Raises:
        ValueError: If the pipeline version is invalid.
    """
    if pipeline_version not in PIPELINE_VERSIONS:
        raise ValueError(f"Invalid pipeline version: {pipeline_version}")

    filter_items(items, "version", lambda version: version == pipeline_version)


def filter_sdk_version(items: list, sdk_version: str, sdk_param: str):
    """Filter the items based on the SDK version.

    Args:
        items (list): The list of items to filter.
        sdk_version (str): The SDK version to filter by.

    Raises:
        ValueError: If the SDK version is invalid.
    """
    if sdk_version not in SDK_VERSIONS:
        raise ValueError(f"Invalid SDK version: {sdk_version}")

    from aixplain.v2.resource import BaseResource

    def predicate(param: Any):
        # v1 SDK uses factory classes (NOT BaseResource subclasses)
        # v2 SDK uses BaseResource subclasses
        return not issubclass(param, BaseResource) if sdk_version == SDK_VERSION_V1 else issubclass(param, BaseResource)

    filter_items(items, sdk_param, predicate)


def pytest_collection_modifyitems(session: pytest.Session, config: pytest.Config, items: list):
    """Modify the items based on the pipeline version and the SDK version.

    Args:
        session (pytest.Session): The pytest session.
        config (pytest.Config): The pytest config.
        items (list): The list of items to modify.

    Raises:
        ValueError: If the pipeline version or the SDK version is invalid.
    """
    pipeline_version = config.getoption(f"{PIPELINE_VERSION_ARG}")
    sdk_version = config.getoption(f"{SDK_VERSION_ARG}")

    if pipeline_version:
        filter_pipeline_version(items, pipeline_version)

    if sdk_version:
        sdk_param = config.getoption(f"{SDK_VERSION_PARAM_ARG}")
        if not sdk_param:
            raise ValueError(f"{SDK_VERSION_PARAM_ARG} parameter is required when using {SDK_VERSION_ARG}")
        filter_sdk_version(items, sdk_version, sdk_param)
