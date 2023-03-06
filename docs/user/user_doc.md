# User Documentaion
aiXplain platform has a vast repository of multiple assets like Models, Datasets, Metrics, Pipelines, etc. The factories in aiXtend SDK provide a powerful set of tools for creating, searching, and managing these assets.

The assets currently supported by the SDK are:
- [Models](#models)
- [Pipelines](#pipelines)
- [Datasets](#datasets)
- [Metrics](#metrics)
- [Benchmarks](#benchmarks)

## Models
aiXplain has an ever-expanding catalog of 35,000+ ready-to-use AI models for various tasks like Translation, Speech Recognition, Diacritization, Sentiment Analysis and much more.

#### Explore
There are two ways to explore our model repository:

The catalog of all available models can be accessed and browsed on the aiXplain platform [here](https://platform.aixplain.com/discovery/models). Details of the model can be found by clicking on the model card. Model ID can be found from the url (`https://platform.aixplain.com/discovery/models/<MODEL_ID>`) or below the model name(refer the image below)

<p align="center">
<img src="../assets/model-id-on-platform.png" height="40%" width="40%" />
</p>

Once the Model ID of the desired model is available, it can be used to create a `Model` Object from the `ModelFactory`. 
```python
from aixtend.factories.model_factory  import ModelFactory
model = ModelFactory.create_asset_from_id(<MODEL_ID>) 
```

Or if you need, the aiXtend SDK allows search for existing models that match a specific criteria. `ModelFactory` can  search for machine learning models that perform a particular task and optionally support a specific input/output language pair. 

```python
from aixtend.factories.model_factory  import ModelFactory
model_list = ModelFactory.get_first_k_assets(k=5, task="translation", input_language="en", output_language="hi")
```
#### Run
The aiXtend SDK allows you to run machine learning models synchronously or asynchronously, depending on your use case. This flexibility allows you to choose the most appropriate mode of execution based on your application's requirements.

```python
# Run Synchronously
translation = model.run("This is a sample text")

# Run Asynchronously
## Start async job
start_response = model.run_async("This is a sample text")
poll_url = start_response["url"]
## Poll to see current job status
poll_response = model.poll(poll_url)
```

## Pipelines
[Design](https://aixplain.com/platform/studio/) is aiXplain’s no-code/low-code AI pipeline builder tool that accelerates AI development by providing a seamless experience to build complex AI systems and deploy them within minutes. You can visit our platform and design your own custom pipeline [here](https://platform.aixplain.com/dashboard/pipelines).

#### Explore
There are two ways to find pipelines:

The catalog of all your pipelines can be accessed and browsed on the aiXplain platform [here](https://platform.aixplain.com/dashboard/pipelines). Details of the pipeline can be found by clicking on the pipeline card. Pipeline ID can be found from the url(`https://platform.aixplain.com/dashboard/pipelines/<PIPELINE_ID>`) or below the pipeline name(just like Models)

Once the Pipeline ID of the desired pipeline is available, it can be used to create a `Pipeline` Object from the `PipelineFactory`. 
```python
from aixtend.factories.pipeline_factory  import PipelineFactory
pipeline = PipelineFactory.create_asset_from_id(<PIPELINE_ID>) 
```

Or if you need, the aiXtend SDK allows search for existing pipelines. 

```python
from aixtend.factories.pipeline_factory  import PipelineFactory
pipeline_list = PipelineFactory.get_first_k_assets(k=5)
```
#### Run
The aiXtend SDK allows you to run pipelines synchronously or asynchronously, depending on your use case. This flexibility allows you to choose the most appropriate mode of execution based on your application's requirements.

```python
# Run Synchronously
result = pipeline.run("This is a sample text")

# Run Asynchronously
## Start async job
start_response = pipeline.run_async("This is a sample text")
poll_url = start_response["url"]
## Poll to see current job status
poll_response = pipeline.poll(poll_url)
```

## Datasets
aiXplain has an extensive collection of Datasets for various tasks like Translation, Speech Recognition, Diacritization, Sentiment Analysis and much more.
You can even upload your own dataset on the platform [here](https://platform.aixplain.com/dashboard/datasets/upload).

The catalog of all available datasets can be accessed and browsed on the aiXplain platform [here](https://platform.aixplain.com/discovery/datasets).

The aiXtend SDK allows search for existing datasets that match a specific criteria. `DatasetFactory` can  search for datasets that are linked to a particular machine learning task and optionally support a specific input/output language pair. 

```python
from aixtend.factories.dataset_factory  import DatasetFactory
dataset_list = DatasetFactory.get_first_k_assets(k=5, task="translation", input_language="en", output_language="fr")
```
Note: This does not download datasets to your local machine.

## Metrics
aiXplain has an impressive library of metrics for various machine learning tasks like Translation, Speech Recognition, Diacritization and Sentiment Analysis. We have reference similarity metrics, human evaluation estimation metrics, and referenceless metrics.

The catalog of all available metrics can be accessed and browsed on the aiXplain platform [here](https://platform.aixplain.com/discovery/metrics).

The aiXtend SDK allows search for existing metrics. `MetricFactory` can  search for metrics for a particular machine learning task.

```python
from aixtend.factories.metric_factory  import MetricFactory
metric_list = MetricFactory.list_assets(task="translation")
```

## Benchmarks

The [aiXplain platform](https://aixplain.com/platform/benchmark) provides a powerful set of tools for benchmarking machine learning models and evaluating their performance on specific tasks. You can obtain easy-to-interpret granular insights on the performance of models for quality, latency, footprint, cost, and bias with our interactive Benchmark reports.

The proposed benchmarking framework is designed for being modular and interoperable in its core across three main components (models, datasets, metrics) in its body to become a one-stop shop for all possible benchmarking activities across several domains and metrics. You need to choose these three components for the task of your choice. 

*Currently Supported tasks are*:  Translation, Speech Recognition, Diacritization and Sentiment Analysis with many more in works.

### Creating a Benchmark
You can create a benchmarking job from our platform [here](https://platform.aixplain.com/benchmark) or you can also use the SDK. Let's see how we can use the `BenchmarkFactory` in the aiXtend SDK for the same. 


```python
from aixtend.factories.dataset_factory  import DatasetFactory
from aixtend.factories.metric_factory  import MetricFactory
from aixtend.factories.model_factory  import ModelFactory
from aixtend.factories.benchmark_factory  import BenchmarkFactory

# Choose 'one or more' models
model_list = ModelFactory.get_first_k_assets(k=5, task="translation", input_language="en", output_language="fr")
# Choose 'one or more' metrics
metric_list = MetricFactory.list_assets(task="translation")
# Choose 'exactly one' dataset
dataset_list = DatasetFactory.get_first_k_assets(k=1, task="translation", input_language="en", output_language="fr")

benchmark = BenchmarkFactory.create_benchmark(<UNIQUE_NAME_OF_BENCHMARK>, dataset_list, model_list, metric_list)
```
For more details on [models](#models), [datasets](#datasets) and [metrics](#metrics) you can visit their docs.

### Running a Benchmark
Once a `Benchmark` is created(refer the [section above](#creating-a-benchmark)), we need to start a new `BenchmarkJob` from it. It is really simple to run a benchmark:
```python
benchmark_job = BenchmarkFactory.start_benchmark_job(benchmark)
```
You can start multiple jobs on a single `Benchmark`.

### Getting the Results 
Once a `BenchmarkJob` is up and running(refer the [section above](#running-a-benchmark)), we can download the current results(even for an In-Progress Job) as a CSV.
```python
results_path = BenchmarkFactory.download_results_as_csv(benchmark_job)
```
