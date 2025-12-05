---
sidebar_label: mixins
title: aixplain.modules.pipeline.designer.mixins
---

### LinkableMixin Objects

```python
class LinkableMixin()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/designer/mixins.py#L5)

Linkable mixin class, this class will be used to link the output of the
node to the input of another node.

This class will be used to link the output of the node to the input of
another node.

#### link

```python
def link(to_node: Node, from_param: Union[str, Param],
         to_param: Union[str, Param]) -> Link
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/designer/mixins.py#L14)

Link the output of the node to the input of another node. This method

will link the output of the node to the input of another node.

**Arguments**:

- `to_node`: the node to link to the output
- `from_param`: the output parameter or the code of the output
parameter
- `to_param`: the input parameter or the code of the input parameter

**Returns**:

the link

### RoutableMixin Objects

```python
class RoutableMixin()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/designer/mixins.py#L39)

Routable mixin class, this class will be used to route the input data to
different nodes based on the input data type.

#### route

```python
def route(*params: Param) -> Node
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/designer/mixins.py#L45)

Route the input data to different nodes based on the input data type.

This method will automatically link the input data to the output data
of the node.

**Arguments**:

- `params`: the output parameters

**Returns**:

the router node

### OutputableMixin Objects

```python
class OutputableMixin()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/designer/mixins.py#L63)

Outputable mixin class, this class will be used to link the output of the
node to the output node of the pipeline.

#### use\_output

```python
def use_output(param: Union[str, Param]) -> Node
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/designer/mixins.py#L69)

Use the output of the node as the output of the pipeline.

This method will automatically link the output of the node to the
output node of the pipeline.

**Arguments**:

- `param`: the output parameter or the code of the output parameter

**Returns**:

the output node

