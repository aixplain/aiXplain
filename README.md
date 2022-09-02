# aiXplain Pipelines 

aiXplain Pipelines enables python programmers to add AI functions to their software.

An aiXplain pipeline is a directed graph (DAG) of AI functions built using aiXplain's designer UI. An AI function is a data processing step that relies on a machine learning model to execute. An example of an AI function is speech recognition or machine translation. Pipelines help you process your data by calling a series of functions as defined in the DAG, abstracting the orchestration, and providing a simple python function call.

aiXplain has a collection of AI models for each AI function. You can explore the collection of our AI models by using the discover feature of our [platform's website](https://platform.aixplain.com/). Also, you can run a model using simple python code.

## aiXplain Pipeline Designer DAG

The image below shows a sample aiXplain pipeline built for subtitling video files. The description of the pipeline can be found in the [documentation](docs/samples/subtitle_generator/README.md).

<img src="docs/assets/designer-subtitling-sample.png" width=30% height=30%>


## Installation

```
pip install aixplain
```

## User Guide

In order to use aiXplain, you need to create an account in [aiXplain platform](https://platform.aixplain.com/). Follow the code samples listed below to get started.

### Code Samples and Demos

aixplain provides python APIs to call AI workflows you can build with aiXplain designer and to call models you subscribed with aiXplain discover.

#### Pipeline Snippet

```
from aixplain.factories.pipeline_factory import PipelineFactory

api_key=<API_KEY>

pipe = PipelineFactory.initialize(api_key=api_key)

path=<DATA_URL>
response = pipe.run(data=path)
```
#### Model Snippet

```
from aixplain.factories.model_factory import ModelFactory

api_key=<API_KEY>

model = ModelFactory.initialize(api_key=api_key)

path=<DATA_URL>
response = model.run(data=path)
```

API_KEY can be obtained by creating a pipeline in pipeline designer through the aiXplain platform UI.   
For DATA_URL generate a http(s) link to your image or video file to process, though text input can be directly supplied to data parameter in the run function without needing a URL.  
  
Information on how to generate the API_KEY can be found in the [subtitle generation pipeline sample video](https://aixplain.com/designer-tutorial/). 

#### Subtitle Generation

This demo creates a .srt file for the supplied video using aixplain-pipelines. Follow the instructions in the [documentation](docs/samples/subtitle_generator/README.md).

## Developer Guide

Follow the developer guide [documentation](docs/development/developer_guide.md).

## Support

Raise issues for support in this repository.  
Pull requests are welcome!
