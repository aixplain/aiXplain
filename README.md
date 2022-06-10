# aiXplain Pipelines 

aiXplain Pipelines enables python programmers to add AI functions
to their software.

An aiXplain pipeline is a directed acyclic graph (DAG) of AI functions built using aiXplain's designer UI. An AI function is a data processing step that relies on a machine learning model to execute. An example of an AI function is speech recognition or machine translation. It helps you process your data by calling a series of functions as defined in the DAG, abstracting the orchestration by providing a simple python function call.

aiXplain has a collection of AI models for each AI function. You can explore the collection of our AI models by using the discover feature of our [platform's website](https://platform.aixplain.com/).

## aiXplain Pipeline Designer DAG

The image below shows a sample aiXplain pipeline built for subtitling video files.

<img src="docs/assets/designer-subtitling-sample.png" width=30% height=30%>


## Installation

```
pip install aixplain-pipelines
```

## User Guide

In order to use aiXplain pipelines, you need to create an account in [aiXplain platform](https://platform.aixplain.com/). Follow the code samples listed below to get started.

### Code Samples and Demos

aixplain-pipelines provides python APIs to call AI workflows you can build with aiXplain designer. 
#### Subtitle Generation

This demo creates a `.srt` file for the supplied video using aixplain-pipelines. Follow the instructions in the [documentation](docs/samples/subtitle_generator/README.md).

## Developer Guide

Follow the developer guide [documentation](docs/developer_guide.md).

## Support

Raise issues for support in this same repositories.
Pull requests are welcome!
