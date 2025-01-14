from typing import List, TYPE_CHECKING
from typing_extensions import Unpack

from aixplain.v2.resource import (
    BaseResource,
    GetResourceMixin,
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

        return Benchmark(BenchmarkFactory.get(benchmark_id=kwargs["id"]))

    @classmethod
    def create(cls, **kwargs: Unpack[BenchmarkCreateParams]) -> "Benchmark":
        from aixplain.factories import BenchmarkFactory

        return Benchmark(BenchmarkFactory.create(**kwargs))

    @classmethod
    def list_normalization_options(cls, metric: "Metric", model: "Model") -> list[str]:
        from aixplain.factories import BenchmarkFactory

        return BenchmarkFactory.list_normalization_options(metric, model)


class BenchmarkJob(
    BaseResource,
    GetResourceMixin[BareGetParams, "BenchmarkJob"],
):
    RESOURCE_PATH = "sdk/benchmarks/jobs"

    @classmethod
    def get(cls, **kwargs: Unpack[BareGetParams]) -> "BenchmarkJob":
        from aixplain.factories import BenchmarkFactory

        return BenchmarkJob(BenchmarkFactory.get_job(job_id=kwargs["id"]))

    def get_scores(self) -> dict:
        from aixplain.factories import BenchmarkFactory

        return BenchmarkFactory.get_benchmark_job_scores(self.id)
