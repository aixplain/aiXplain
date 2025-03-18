from typing_extensions import Unpack, NotRequired

from aixplain.v2.resource import (
    BaseResource,
    ListResourceMixin,
    GetResourceMixin,
    BareGetParams,
    BaseListParams,
    Page,
)


class MetricListParams(BaseListParams):
    """Parameters for listing metrics.

    Attributes:
        model_id: str: The model ID.
        is_source_required: bool: Whether the source is required.
        is_reference_required: bool: Whether the reference is required.
    """

    model_id: str
    is_source_required: NotRequired[bool]
    is_reference_required: NotRequired[bool]


class Metric(
    BaseResource,
    ListResourceMixin[MetricListParams, "Metric"],
    GetResourceMixin[BareGetParams, "Metric"],
):
    """Resource for metrics."""

    RESOURCE_PATH = "sdk/metrics"

    @classmethod
    def get(cls, id: str, **kwargs: Unpack[BareGetParams]) -> "Metric":
        from aixplain.factories.metric_factory import MetricFactory

        return MetricFactory.get(metric_id=id)

    @classmethod
    def list(cls, **kwargs: Unpack[MetricListParams]) -> Page["Metric"]:
        from aixplain.factories.metric_factory import MetricFactory

        kwargs.setdefault("is_source_required", None)
        kwargs.setdefault("is_reference_required", None)
        kwargs.setdefault("page_number", cls.PAGINATE_DEFAULT_PAGE_NUMBER)
        kwargs.setdefault("page_size", cls.PAGINATE_DEFAULT_PAGE_SIZE)

        return MetricFactory.list(**kwargs)
