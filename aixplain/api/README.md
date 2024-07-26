# User Guide for AIXplain API

## Introduction
Aixplan SDK provides a programmatic api to able to build pipelines to build solutions for the AIXplain platform.

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
input = Input(*args, **kwargs)
input.attach(pipeline)
```

or we can use `add_node` method of the pipeline:

```python
input = pipeline.add_node(Input(*args, **kwargs))
```

or we can implicity pass pipeline to the node constructor:

```python
input = Input(*args, pipeline=pipeline, **kwargs)
```

or we can instantiate the node directly in the pipeline. Method will accept the node class and the keyword arguments for the node constructor:

```python
input = pipeline.input(*args, **kwargs)
```

Each pipeline should have at least one input, asset and output node.
Output nodes can be added like any other node as shown above.

```python
translation = pipeline.asset(assetId=TRANSLATION_ASSET_ID)
output = pipeline.output(*args, **kwargs)
translation.link(output, 'data', 'output')

```

Output nodes also have a special shortcut syntax for nodes those implements `Outputable` mixin like shown below. This method will implicityly create an output node and link the node to the output node.

```python
output = translation.use_output('parameter_name_we_are_interested_in')
```

### Linking nodes
```python
input = pipeline.input()
translation = pipeline.asset(assetId=TRANSLATION_ASSET_ID)
```

We can use node `link` method to link the nodes together. The `link` method takes the following arguments:

```python
input.link(translation, 'input', 'text')
```

we can explicitly specify from and to parameters by using keyword arguments
`from_param` and `to_param`:


```python
input.link(translation, from_param='output', to_param='input')
```


or we can use parameter instances rather than strings:

```python
input.link(translation, from_param=input.output, to_param=translation.input)
```

or we can even link the parameters directly:

```python
input.output.link(translation.input)
```

### Validating the pipeline
Pipeline provides a `validate` method to validate the pipeline. It will check if the pipeline is valid and if the pipeline is ready to run. Otherwise, it will raise an exception.

```python
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