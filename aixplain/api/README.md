# User Guide for Programmatic API

## Introduction
Aixplan SDK provides a programmatic api to able to create pipelines to build solutions for the Aixplain platform.

### Minimal Example
```python
from aixplain.api import Pipeline

TRANSLATION_ASSET_ID = 'your-translation-asset-id'

pipeline = Pipeline('Transaltion Pipeline')
input = pipeline.input()
translation = pipeline.asset(assetId=TRANSLATION_ASSET_ID)
output = translation.use_output('data')

pipeline.save()
outputs = pipeline.run('This is example text to translate')

print(outputs)
```

### Instantiating nodes
```python
from aixplain.api import Pipeline, Input

pipeline = Pipeline()
```

We can instantiate a node by calling the node class and we can attach the node to the pipeline by calling the `attach` method:

```python
...

input = Input(*args, **kwargs)
input.attach(pipeline)
```

or we can use `add_node` method of the pipeline:

```python
...

input = pipeline.add_node(Input(*args, **kwargs))
```

or we can implicity pass pipeline to the node constructor:

```python
...

input = Input(*args, pipeline=pipeline, **kwargs)
```

or we can instantiate the node directly in the pipeline. Method will accept the node class and the keyword arguments for the node constructor:

```python
...

input = pipeline.input(*args, **kwargs)
```

Each pipeline should have at least one input, asset and output node.
Output nodes can be added like any other node as shown above.

```python
...

translation = pipeline.asset(assetId=TRANSLATION_ASSET_ID)
output = pipeline.output(*args, **kwargs)
translation.link(output, 'data', 'output')

```

Output nodes also have a special shortcut syntax for nodes those implements `Outputable` mixin like shown below. This method will implicityly create an output node and link the node to the output node.

```python
...

output = translation.use_output('parameter_name_we_are_interested_in')
```

### Asset nodes and automatic population
Asset nodes are the nodes that will be used to run the model. Asset nodes should have an asset id which is used to populate the node with the model information from the Aixplain platform. Once any asset node instantiated, it will contain all the information about the model and its parameters.

```python
...

translation = pipeline.asset(assetId=TRANSLATION_ASSET_ID)
```

Translation node now contains all the information about the model and its parameters. We can access the parameters by using the `inputs` and `outputs` attributes of the node.

```python
...

print(translation.inputValues)
print(translation.outputValues)
```

### Handling parameters
Parameters are the inputs and outputs of the nodes. We can access the parameters by using the `inputs` and `outputs` attributes of the node which behaves like a proxy object to the parameters.

```python
...

print(translation.inputs.text)
print(translation.outputs.data)
```

When required we can add any input or output parameter to the node by using the `add_input_parameter` and `add_output_parameter` methods of the node.

```python
...

translation.add_input_parameter('source_language', DataType.TEXT)
translation.add_output_parameter('source_audio', DataType.AUDIO)
```

Parameters are also can be instantiated directly by using the `InputParam` or `OutputParam` classes like:

```python
from aixplain.api import InputParam, OutputParam

...

# This will automatically add the parameter to the node
source_language = InputParam(
    code='source_language',
    dataType=DataType.TEXT,
    is_required=True,
    node=translation
)
```

# or we can add the parameter to the node explicitly

```python
...

source_audio = OutputParam(dataType=DataType.AUDIO, code='source_audio')
translation.add_param(source_audio)
```

### Linking nodes
Linking nodes are required to pass the data from one node to another. We can link the nodes by using the `link` method. The `link` method will link the output of the first node to the input of the second node on the specified parameters.

Consider the following nodes:
```python
...

input = pipeline.input()
translation = pipeline.asset(assetId=TRANSLATION_ASSET_ID)
```

We can use node `link` method to link the nodes together. The `link` method takes the following arguments:

```python
...

input.link(translation, 'input', 'text')
```

we can explicitly specify from and to parameters by using keyword arguments
`from_param` and `to_param`:


```python
...

input.link(translation, from_param='input', to_param='text')
```


or we can use parameter instances rather than strings:

```python
...

input.link(translation, from_param=input.outputs.input, to_param=translation.inputs.text)
```

or we can even link the parameters directly:

```python
...

input.outputs.input.link(translation.inputs.text)
```

### Validating the pipeline
Pipeline provides a `validate` method to validate the pipeline. It will check if the pipeline is valid and if the pipeline is ready to run. Otherwise, it will raise an exception.

```python
...

pipeline.validate()
```

### Save and run the pipeline

Pipelines should be saved before running. The `save` method will save the pipeline to the AIXplain platform. Save method will implicitly call the `validate` method.

`run` method will accept the input data and will return the output data.

```python
pipeline.save()  # any semantic breaks will raise an exception
outputs = pipeline.run('This is example text to translate')
print(outputs)
```