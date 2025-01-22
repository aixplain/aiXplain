from typing import List
from typing_extensions import Unpack, NotRequired

from aixplain.v2.resource import (
    BaseResource,
    ListResourceMixin,
    GetResourceMixin,
    BareGetParams,
    BaseListParams,
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

    def get(self, **kwargs: Unpack[BareGetParams]) -> "Metric":
        from aixplain.factories.metric_factory import MetricFactory

        return Metric(MetricFactory.get(metric_id=kwargs["metric_id"]))

    def list(self, **kwargs: Unpack[MetricListParams]) -> List["Metric"]:
        from aixplain.factories.metric_factory import MetricFactory

        kwargs.setdefault("is_source_required", None)
        kwargs.setdefault("is_reference_required", None)
        return [Metric(metric) for metric in MetricFactory.list(**kwargs)]
