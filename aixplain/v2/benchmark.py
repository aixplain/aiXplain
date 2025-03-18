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
    """Parameters for creating a benchmark.

    Attributes:
        name: str: The name of the benchmark.
        dataset_list: List["Dataset"]: The list of datasets.
        model_list: List["Model"]: The list of models.
        metric_list: List["Metric"]: The list of metrics.
    """

    name: str
    dataset_list: List["Dataset"]
    model_list: List["Model"]
    metric_list: List["Metric"]


class Benchmark(
    BaseResource,
    GetResourceMixin[BareGetParams, "Benchmark"],
    CreateResourceMixin[BenchmarkCreateParams, "Benchmark"],
):
    """Resource for benchmarks."""

    RESOURCE_PATH = "sdk/benchmarks"

    @classmethod
    def get(cls, id: str, **kwargs: Unpack[BareGetParams]) -> "Benchmark":
        from aixplain.factories import BenchmarkFactory

        return BenchmarkFactory.get(benchmark_id=id)

    @classmethod
    def create(cls, *args, **kwargs: Unpack[BenchmarkCreateParams]) -> "Benchmark":
        from aixplain.factories import BenchmarkFactory

        return BenchmarkFactory.create(*args, **kwargs)

    @classmethod
    def list_normalization_options(cls, metric: "Metric", model: "Model") -> List[str]:
        """
        List the normalization options for a metric and a model.

        Args:
            metric: "Metric": The metric.
            model: "Model": The model.

        Returns:
            List[str]: The list of normalization options.
        """
        from aixplain.factories import BenchmarkFactory

        return BenchmarkFactory.list_normalization_options(metric, model)


class BenchmarkJob(
    BaseResource,
    GetResourceMixin[BareGetParams, "BenchmarkJob"],
):
    """Resource for benchmark jobs."""

    RESOURCE_PATH = "sdk/benchmarks/jobs"

    @classmethod
    def get(cls, **kwargs: Unpack[BareGetParams]) -> "BenchmarkJob":
        from aixplain.factories import BenchmarkFactory

        return BenchmarkFactory.get_job(job_id=kwargs["id"])

    def get_scores(self) -> dict:
        """
        Get the scores for a benchmark job.

        Returns:
            dict: The scores.
        """
        from aixplain.factories import BenchmarkFactory

        return BenchmarkFactory.get_benchmark_job_scores(self.id)
