from typing import List, TYPE_CHECKING
from typing_extensions import Unpack

from aixplain.v2.resource import (
    BaseResource,
    ListResourceMixin,
    GetResourceMixin,
    BaseListParams,
    BareGetParams,
    CreateResourceMixin,
    BareCreateParams,
)

if TYPE_CHECKING:
    from aixplain.modules.metric import Metric
    from aixplain.modules.model import Model
    from aixplain.modules.dataset import Dataset


class BenchmarkCreateParams(BareCreateParams):
    name: str
    dataset_list: List["Dataset"]
    model_list: List["Model"]
    metric_list: List["Metric"]


class Benchmark(
    BaseResource,
    GetResourceMixin[BareGetParams, "Benchmark"],
    CreateResourceMixin[BenchmarkCreateParams, "Benchmark"],
):
    RESOURCE_PATH = "sdk/benchmarks"

    @classmethod
    def get(cls, **kwargs: Unpack[BareGetParams]) -> "Benchmark":
        from aixplain.factories import BenchmarkFactory

        return BenchmarkFactory.get(benchmark_id=kwargs["id"])

    @classmethod
    def create(cls, **kwargs: Unpack[BenchmarkCreateParams]) -> "Benchmark":
        from aixplain.factories import BenchmarkFactory

        return BenchmarkFactory.create(**kwargs)


class BenchmarkJob(
    BaseResource,
    GetResourceMixin[BareGetParams, "BenchmarkJob"],
):
    RESOURCE_PATH = "sdk/benchmarks/jobs"

    @classmethod
    def get(cls, **kwargs: Unpack[BareGetParams]) -> "BenchmarkJob":
        from aixplain.factories import BenchmarkFactory

        return BenchmarkFactory.get_job(job_id=kwargs["id"])

    @classmethod
    def get_scores(cls, **kwargs: Unpack[BareGetParams]) -> "BenchmarkJob":
        from aixplain.factories import BenchmarkFactory

        return BenchmarkFactory.get_benchmark_job_scores(job_id=kwargs["id"])


class NormalizationOptionListParams(BaseListParams):
    metric: "Metric"
    model: "Model"


class NormalizationOption(
    BaseResource,
    ListResourceMixin[NormalizationOptionListParams, "NormalizationOption"],
):
    RESOURCE_PATH = "sdk/benchmarks/normalization-options"

    @classmethod
    def list(
        cls, **kwargs: Unpack[NormalizationOptionListParams]
    ) -> List["NormalizationOption"]:
        from aixplain.factories import BenchmarkFactory

        return BenchmarkFactory.list_normalization_options(
            metric=kwargs["metric"], model=kwargs["model"]
        )
