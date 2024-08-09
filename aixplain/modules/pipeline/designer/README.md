# Aixplan SDK User Guide

## Introduction

Aixplan SDK provides a programmatic API to create pipelines for building solutions on the Aixplain platform.

## Minimal Example

Here's a quick example to get you started:

```python
from aixplain.factories.pipeline_factory import PipelineFactory

TRANSLATION_ASSET_ID = 'your-translation-asset-id'

pipeline = PipelineFactory.init('Translation Pipeline')
input_node = pipeline.input()
translation_node = pipeline.translation(assetId=TRANSLATION_ASSET_ID)

input_node.link(translation_node, 'input', 'text')

output_node = translation_node.use_output('data')

pipeline.save()
outputs = pipeline.run('This is example text to translate')

print(outputs)
```

## Instantiating Nodes

To create a pipeline and instantiate nodes, use the following code:

```python
from aixplain.factories.pipeline_factory import PipelineFactory
from aixplain.modules.pipeline.designer import Input

pipeline = PipelineFactory.init("My Pipeline")
input_node = Input(*args, **kwargs)
input_node.attach(pipeline)
```

Alternatively, add nodes to the pipeline using `add_node`:

```python
input_node = pipeline.add_node(Input(*args, **kwargs))
```

You can also pass the pipeline to the node constructor:

```python
input_node = Input(*args, pipeline=pipeline, **kwargs)
```

Or directly instantiate the node within the pipeline:

```python
input_node = pipeline.input(*args, **kwargs)
```

## Adding Output Nodes

Each pipeline should have at least one input, asset, and output node. Add output nodes like any other node:

```python
translation_node = pipeline.translation(assetId=TRANSLATION_ASSET_ID)
output_node = pipeline.output(*args, **kwargs)
translation_node.link(output_node, 'data', 'output')
```

For nodes implementing the `Outputable` mixin, use the shortcut syntax:

```python
output_node = translation_node.use_output('parameter_name_we_are_interested_in')
```

## Asset Nodes and Automatic Population

Asset nodes are used to run models and should have an asset ID. Once instantiated, an asset node contains all model information and parameters which is populated automatically by interacting with the Aixplain platform.

```python
translation_node = pipeline.translation(assetId=TRANSLATION_ASSET_ID)
print(translation_node.inputs)
print(translation_node.outputs)
```

## Handling Parameters

Parameters are accessed via the `inputs` and `outputs` attributes of the node, behaving as proxy objects to the parameters.

```python
print(translation_node.inputs.text)
print(translation_node.outputs.data)
```

Add parameters to a node using `create_param` on corresponding `inputs` or `outputs` attribute:

```python
translation_node.inputs.create_param('source_language', DataType.TEXT)
translation_node.outputs.create_param('source_audio', DataType.AUDIO)
```

Alternatively, instantiate parameters directly using `InputParam` or `OutputParam` classes:

```python
from aixplain.modules.pipeline.designer import InputParam, OutputParam

source_language = InputParam(
    code='source_language',
    dataType=DataType.TEXT,
    is_required=True,
    node=translation_node
)
```

Or add parameters explicitly:

```python
source_audio = OutputParam(dataType=DataType.AUDIO, code='source_audio')
translation_node.outputs.add_param(source_audio)
```

In case of need, any parameter value can be set directly without requiring node linking:

```python
translation_node.inputs.text = 'This is example text to translate'
translation_node.inputs.source_language = 'en'
```

This will implicity set the `value` attribute of the parameter object.

## Linking Nodes

Link nodes to pass data between them using the `link` method. This method links the output of one node to the input of another on specified parameters.

Consider the following nodes:

```python
input_node = pipeline.input()
translation_node = pipeline.translation(assetId=TRANSLATION_ASSET_ID)
```

Link nodes together:

```python
input_node.link(translation_node, 'input', 'text')
```

Specify parameters explicitly:

```python
input_node.link(translation_node, from_param='input', to_param='text')
```

Or use parameter instances:

```python
input_node.link(translation_node, from_param=input_node.outputs.input, to_param=translation_node.inputs.text)
```

You can also link parameters directly if you find it more convenient:

```python
input_node.outputs.input.link(translation_node.inputs.text)
```

## Validating the Pipeline

Use the `validate` method to ensure the pipeline is valid and ready to run. This method raises an exception if the pipeline has issues.

```python
pipeline.validate()
```

This method will check the following:
 * Contains at least one input, asset, and output node
 * All input nodes are linked in, output nodes are linked out, and rest are linked in and out
 * All links pointing to the correct nodes and corresponding params.
 * All required params are either set or linked
 * All linked params have the same data type

Otherwise raises `ValueError` with a cause if the pipeline is not valid.

## Save and Run the Pipeline

Save the pipeline before running it. The `save` method implicitly calls the `validate` method. Use the `run` method to execute the pipeline with input data.

```python
pipeline.save() # Raises an exception if there are semantic issues
outputs = pipeline.run('This is example text to translate')
print(outputs)
```

This guide covers the basic usage of the programmatic api of Aixplan SDK for creating and running pipelines. For more advanced features, refer to the code itself.