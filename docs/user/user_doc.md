# User Documentaion
aiXplain platform has a vast repository of multiple assets like Models, Datasets, Metrics, Pipelines, etc. The factories in aiXtend SDK provide a powerful set of tools for creating, searching, and managing these assets.

The assets currently supported by the SDK are:
- [Models](#models)
- [Pipelines](#pipelines)
- Datasets
- Metrics
- Benchmarks

## Models
aiXplain has an ever-expanding catalog of 35,000+ ready-to-use AI models for various tasks like Translation, Speech Recognition,  Diacritization, Sentiment Analysis and much more.

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
