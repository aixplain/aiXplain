---
sidebar_label: nodes
title: aixplain.modules.pipeline.designer.nodes
---

### AssetNode Objects

```python
class AssetNode(Node[TI, TO], LinkableMixin, OutputableMixin)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/designer/nodes.py#L26)

Asset node class, this node will be used to fetch the asset from the
aixplain platform and use it in the pipeline.

`assetId` is required and will be used to fetch the asset from the
aixplain platform.

Input and output parameters will be automatically added based on the
asset function spec.

### Input Objects

```python
class Input(Node[InputInputs, InputOutputs], LinkableMixin, RoutableMixin)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/designer/nodes.py#L184)

Input node class, this node will be used to input the data to the
pipeline.

Input nodes has only one output parameter called `input`.

`data` is a special convenient parameter that will be uploaded to the
aixplain platform and the link will be passed as the input to the node.

### Output Objects

```python
class Output(Node[OutputInputs, OutputOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/designer/nodes.py#L236)

Output node class, this node will be used to output the result of the
pipeline.

Output nodes has only one input parameter called `output`.

### Script Objects

```python
class Script(Node[TI, TO], LinkableMixin, OutputableMixin)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/designer/nodes.py#L259)

Script node class, this node will be used to run a script on the input
data.

`script_path` is a special convenient parameter that will be uploaded to
the aixplain platform and the link will be passed as the input to the node.

### Route Objects

```python
class Route(Serializable)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/designer/nodes.py#L299)

Route class, this class will be used to route the input data to different
nodes based on the input data type.

#### \_\_init\_\_

```python
def __init__(value: DataType, path: List[Union[Node, int]],
             operation: Operation, type: RouteType, **kwargs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/designer/nodes.py#L310)

Post init method to convert the nodes to node numbers if they are
nodes.

### Router Objects

```python
class Router(Node[RouterInputs, RouterOutputs], LinkableMixin)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/designer/nodes.py#L352)

Router node class, this node will be used to route the input data to
different nodes based on the input data type.

### Decision Objects

```python
class Decision(Node[DecisionInputs, DecisionOutputs], LinkableMixin)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/designer/nodes.py#L391)

Decision node class, this node will be used to make decisions based on
the input data.

### BaseSegmentor Objects

```python
class BaseSegmentor(AssetNode[TI, TO])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/designer/nodes.py#L441)

Segmentor node class, this node will be used to segment the input data
into smaller fragments for much easier and efficient processing.

### BareSegmentor Objects

```python
class BareSegmentor(BaseSegmentor[SegmentorInputs, SegmentorOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/designer/nodes.py#L463)

Segmentor node class, this node will be used to segment the input data
into smaller fragments for much easier and efficient processing.

### BaseReconstructor Objects

```python
class BaseReconstructor(AssetNode[TI, TO])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/designer/nodes.py#L475)

Reconstructor node class, this node will be used to reconstruct the
output of the segmented lines of execution.

### BareReconstructor Objects

```python
class BareReconstructor(BaseReconstructor[ReconstructorInputs,
                                          ReconstructorOutputs])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/designer/nodes.py#L493)

Reconstructor node class, this node will be used to reconstruct the
output of the segmented lines of execution.

