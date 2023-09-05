# User Documentation
aiXplain has a vast repository of multiple assets such as models, corpus, datasets, metrics, pipelines, and more. The factories in aiXplain SDK provide a powerful set of tools for creating, searching, and managing these assets.

The assets and services currently supported by the SDK are:
#### Assets
- [Model](#models)
- [Pipeline](#pipelines)
- [Corpus](#corpus)
- [Dataset](#datasets)
- [Metric](#metrics)
#### Services
- [Benchmark](#benchmark)
- [FineTune](#finetune)

## Models
aiXplain has an ever-expanding catalog of 35,000+ ready-to-use AI models to be used for various tasks like Translation, Speech Recognition, Diacritization, Sentiment Analysis, and much more.

### Explore
There are two ways to explore our model repository:

*1. Through the UI:*

The catalog of all available models on aiXplain can be accessed and browsed [here](https://platform.aixplain.com/discovery/models). Details of each model can be found by clicking on the model card. Model ID can be found on the URL or below the model name.

Please refer to the image below.

<img src="../assets/model-id-on-platform.png" height="40%" width="40%" />

Once the Model ID of the desired model is available, it can be used to create a `Model` object from the `ModelFactory`.
```python
from aixplain.factories import ModelFactory
model = ModelFactory.get(<MODEL_ID>) 
```

*2. Through the SDK:*

If you need, the aixplain SDK allows searching for existing models that match a specific criteria. `ModelFactory` can search for machine learning models that perform a particular task and optionally support a specific input/output language pair.

```python
from aixplain.factories import ModelFactory
from aixplain.enums import Function, Language
model_list = ModelFactory.list(function=Function.TRANSLATION, source_languages=Language.English, target_languages=Language.French)["results"]
```

### Run
The aixplain SDK allows you to run machine learning models synchronously or asynchronously, depending on your use case. This flexibility allows you to choose the most appropriate mode of execution based on your application's requirements.

```python
# Run Synchronously
translation = model.run("This is a sample text") # You can use a URL or a file path on your local machine

# Run Asynchronously
## Start async job
start_response = model.run_async("This is a sample text")
poll_url = start_response["url"]
## Poll to see current job status
poll_response = model.poll(poll_url)
```

## Pipelines
[Design](https://aixplain.com/platform/studio/) is aiXplain’s no-code AI pipeline builder tool that accelerates AI development by providing a seamless experience to build complex AI systems and deploy them within minutes. You can visit our platform and design your own custom pipeline [here](https://platform.aixplain.com/studio).

### Explore
There are two ways to find pipelines:

*1. Through the UI:*

The catalog of all your pipelines on aiXplain can be accessed and browsed [here](https://platform.aixplain.com/dashboard/pipelines). Details of the pipeline can be found by clicking on the pipeline card. Pipeline ID can be found from the URL or below the pipeline name (similar to models).

Once the Pipeline ID of the desired pipeline is available, it can be used to create a `Pipeline` object from the `PipelineFactory`. 
```python
from aixplain.factories import PipelineFactory
pipeline = PipelineFactory.get(<PIPELINE_ID>) 
```

*2. Through the SDK:*

If you need, the aixplain SDK allows searching for existing pipelines. 

```python
from aixplain.factories import PipelineFactory
pipeline_list = PipelineFactory.get_first_k_assets(k=5)
```

### Run
The aixplain SDK allows you to run pipelines synchronously or asynchronously, depending on your use case. This flexibility allows you to choose the most appropriate mode of execution based on your application's requirements.

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

For multi-input pipelines, you can specify as input a dictionary where the keys are the label names of the input node and values are their corresponding content:

```python
# Run Synchronously
result = pipeline.run({ 
    "Input 1": "This is a sample text to input node 1.",
    "Input 2": "This is a sample text to input node 2."
})
```

### Process Data Assets

You can also process an aiXplain data asset, being a Corpus or a Dataset, using a pipeline. For this end, just specify the ID of the data asset and the ID of its corresponding data to be processed. For example:

```python
# Run Synchronously
result = pipeline.run(data="64acbad666608858f693a3a0", data_asset="64acbad666608858f693a39f")

# Run Asynchronously
## Start async job
start_response = pipeline.run_async(data="64acbad666608858f693a3a0", data_asset="64acbad666608858f693a39f")
poll_url = start_response["url"]
## Poll to see current job status
poll_response = pipeline.poll(poll_url)
```

## Corpus

aiXplain has an extensive collection of general-purpose corpora to be explored, processed and used to create task-specific datasets.

The aiXplain SDK allows searching for existing corpora that match a specific criteria. `CorpusFactory` can search for corpora that contain data from a particular language pair or data type.

```python
from aixplain.enums import DataType, Language
from aixplain.factories import CorpusFactory
corpus_list = CorpusFactory.list(page_size=5, language=Language.English, data_type=DataType.AUDIO)["results"]
```
Note: This does not download the resulted corpora to your local machine.

### Corpus Onboarding

Using the aiXplain SDK, you can also onboard your corpus into the aiXplain platform. A step-by-step example on how to do it can be accessed here:

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/drive/1-FYTtyVaDxyVv7kGCaMEd5E3uiHYHRTt?usp=sharing)

### Label Studio Corpus Onboarding

The Label Studio platform encompasses distinct projects, each distinguished by the Label Studio authentication API key employed. Within these projects, a variety of tasks are hosted, often spanning multiple data types. The `LabelStudioFactory` class has been crafted to adeptly retrieve and manage both audio and text data, whether originating from a Label Studio task or a project.

For successful utilization of this class, the requisites are straightforward: you must possess the relevant Label Studio project or task ID, as well as the corresponding Label Studio authentication API key. This process is further elaborated through a step-by-step example which can be found below:

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/drive/1uuvRoGbQ9tu_An5EACWtZnf20cDF5l3j) 

## Datasets
Different from corpus, a dataset is a representative sample of a specific phenomenon to a specific AI task. aiXplain also counts with an extensive collection of datasets for training, infer and benchmark various tasks like Translation, Speech Recognition, Diacritization, Sentiment Analysis, and much more.
You can even upload your own dataset [here](https://platform.aixplain.com/dashboard/datasets/upload).

The catalog of all available datasets on aiXplain can be accessed and browsed [here](https://platform.aixplain.com/discovery/datasets).

The aixplain SDK allows searching for existing datasets that match a specific criteria. `DatasetFactory` can search for datasets that are linked to a particular machine learning task and optionally support a specific input/output language pair.

```python
from aixplain.factories import DatasetFactory
from aixplain.enums import Function, Language
dataset_list = DatasetFactory.list(function=Function.TRANSLATION, source_languages=Language.English, target_languages=Language.French)["results"]
```
Note: This does not download datasets to your local machine.

### Dataset Onboarding

Using the aiXplain SDK, you can also onboard your dataset into the aiXplain platform. A step-by-step example on how to do it can be accessed here:
- Machine translation dataset:
  - [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/drive/1lkw_OW53PGaWE7Khj9JAM8V5y4LFZ8XB?usp=sharing) 


- Speech recognition dataset:
  - [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/drive/1f1NXHGxhIy0AAXnUZJB8QY3JLl-uC37e?usp=sharing) 

- Machine translation dataset directly from s3:
  - [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/drive/1Asnjeq5JQ9pV6UUQ2Z20XtrjnoaFD0nf?usp=sharing) 

## FineTune

[FineTune](https://aixplain.com/platform/finetune) allows you to customize models by tuning them using your data and enhancing their performance. Set up and start fine-tuning with a few lines of code. Once fine-tuning is complete, the model will be deployed into your assets, ready for you to use.

You can also run this FineTune guide in Google Colab:

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/drive/1rVxxZpHzyP4FWn_Rd_j_g8tHU76S3rVT?usp=sharing)

### Creating a FineTune


You can use the `FinetuneFactory` to create a FineTune object using the SDK. For now, we support the following tasks: `translation` and `speech-recognition`:

```python
from aixplain.factories import FinetuneFactory, DatasetFactory, ModelFactory
from aixplain.enums import Function, Language

# Choose 'exactly one' model
model = ModelFactory.list(function=Function.TRANSLATION, source_languages=Language.English, target_languages=Language.French, is_finetunable=True, page_size=1)["results"][0]
# Choose 'one or more' datasets
dataset_list = DatasetFactory.list(function=Function.TRANSLATION, source_languages=Language.English, target_languages=Language.French, page_size=1)["results"]

finetune = FinetuneFactory.create(<UNIQUE_NAME_OF_FINETUNE>, dataset_list, model)
```
You can visit [model](#models) and [dataset](#datasets) docs for more details.

Also, you can check the training, hosting and inference costs by running the following command:
```python
finetune.cost.to_dict()
```
```python
{
  'trainingCost': {
    'total': 0.1,
    'supplierCost': 0,
    'overheadCost': 0.1,
    'willRefundIfLowerThanMax': False,
    'totalVolume': 106.03,
    'unitPrice': 0
  },
  'inferenceCost': [
    {
      'unitPrice': 6e-05,
      'unitType': 'CHAR',
      'volume': 0
    }
  ],
  'hostingCost': {
    'currentMonthPrice': 0,
    'monthlyPrice': 0,
    'pricePerCycle': 0,
    'supplierBillingCycle': 'MONTH',
    'willRefundIfLowerThanMax': False
  }
}
```

### Starting a FineTune

Once a `FineTune` is created (refer to the [section above](#creating-a-finetune)), we need to call the start method:
```python
finetune_model = finetune.start()
```
We receive a model that we can check the fine-tuning status:
 ```python
status = finetune_model.check_finetune_status()
```
Status can be one of the following: `onboarding`, `onboarded`, `hidden`, `training`, `deleted`, `enabling`, `disabled`, `failed`, `deleting`.

Once it is `onboarded`, you are ready to use it as any other model!


## Metrics
aiXplain has an impressive library of metrics for various machine learning tasks like Translation, Speech Recognition, Diacritization, and Sentiment Analysis. There are reference similarity metrics, human evaluation estimation metrics, and referenceless metrics.

The catalog of all available metrics on aiXplain can be accessed and browsed [here](https://platform.aixplain.com/discovery/metrics).

The aixplain SDK allows searching for existing metrics. `MetricFactory` can search for metrics for a particular machine learning task.

```python
from aixplain.factories import MetricFactory
metric_list = MetricFactory.list()['results']
```

### Run
The aixplain SDK allows you to run metrics. Some metrics might also require source or reference as inputs.
```python
output = metric.run("hypothesis": "<sample hypothesis>", "source": "<sample optional source>", "reference": "<sample optional reference>")
```
You can even pass a list of inputs in a single call.
```python
output = metric.run("hypothesis": ["<sample hypothesis 1>", "<sample hypothesis 2>"], "source": ["<sample optional source 1>", "<sample optional source 2>"], "reference": ["<sample optional reference> 1", "<sample optional reference> 2"])
```


## Benchmark

[Benchmark](https://aixplain.com/platform/benchmark) is a powerful tool for benchmarking machine learning models and evaluating their performance on specific tasks. You can obtain easy-to-interpret granular insights on the performance of models for quality, latency, footprint, cost, and bias with our interactive Benchmark reports.

The proposed benchmarking framework is designed for being modular and interoperable in its core across three main components (models, datasets, metrics) in its body to become a one-stop shop for all possible benchmarking activities across several domains and metrics. You need to choose these three components for the task of your choice.

*Currently supported tasks are Translation, Speech Recognition, Diacritization, and Sentiment Analysis with many more in the works.*

### Creating a Benchmark
You can create a benchmarking job on aiXplain [here](https://platform.aixplain.com/benchmark) or you can also use the SDK. Let's see how we can use the `BenchmarkFactory` in the aixplain SDK for the same purpose.

```python
from aixplain.factories import BenchmarkFactory, DatasetFactory, MetricFactory, ModelFactory
from aixplain.enums import Function, Language

# Choose 'one or more' models
models = ModelFactory.list(function=Function.SPEECH_RECOGNITION, source_languages=Language.English_UNITED_STATES, page_size=2)['results']
# Choose 'one or more' metrics that are supported
metrics = MetricFactory.list(model_id=models[0].id, page_size=2)['results']
# Choose 'exactly one' dataset
datasets = DatasetFactory.list(function=Function.SPEECH_RECOGNITION, source_languages=Language.English_UNITED_STATES, page_size=1)['results']

benchmark = BenchmarkFactory.create(<UNIQUE_NAME_OF_BENCHMARK>, dataset_list=datasets, model_list=models, metric_list=metrics)
```

You can visit [model](#models), [dataset](#datasets), and [metric](#metrics) docs for more details.

### Running a Benchmark
Once a `Benchmark` is created (refer to the [section above](#creating-a-benchmark)), we need to start a new `BenchmarkJob` from it. It is really simple to run a benchmark:
```python
benchmark_job = benchmark.start()
```
Note: You can start multiple jobs on a single `Benchmark`.

### Getting the Results 
Once a `BenchmarkJob` is up and running (refer to the [section above](#running-a-benchmark)), we can check the status or directly download the current results as a CSV (even for an in-progress benchmarking job).
#### Status
```python
status = benchmark_job.check_status()
```
#### Results
```python
results_path = benchmark_job.download_results_as_csv()
```

### Adding Normalization To Your Benchmark
We have methods that specialize in handling text data from various languages, providing both general and tailored preprocessing techniques for each language's unique characteristics. These are called normalization options. The normalization process transforms raw text data into a standardized format, enabling a fair and exact evaluation of performance across diverse models. A few examples are 'removing numbers' and 'lowercase text'.
To get the list of supported normalization options, we need the metric and the model that we are going to use in benchmarking.
```python
supported_options = BenchmarkFactory.list_normalization_options(metric, model)
```
Note: These options can be different for each metric in the same benchmark

You have the flexibility to choose multiple normalization options for each performance metric. You can also opt for the same metric with varying sets of normalization options. This adaptability provides a thorough and comprehensive way to compare model performance.
```python
selected_options = [<option 1>....<option N>]
metric.add_normalization_options(selected_options)
```
You can even select multiple configurations for the same metric
```python
selected_options_config_1 = [<option 1>, <option 2>, <option 3>]
selected_options_config_2 = [<option 3>, <option 4>]
metric.add_normalization_options(selected_options_config_1)
metric.add_normalization_options(selected_options_config_2)
```
After this you can create the benchmark normally
```python
benchmark = BenchmarkFactory.create(<UNIQUE_NAME_OF_BENCHMARK>, dataset_list=datasets, model_list=models, metric_list=metrics_with_normalization)
```
