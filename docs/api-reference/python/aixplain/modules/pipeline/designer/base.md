---
sidebar_label: base
title: aixplain.modules.pipeline.designer.base
---

### Param Objects

```python
class Param(Serializable)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/designer/base.py#L28)

Param class, this class will be used to create the parameters of the node.

#### attach\_to

```python
def attach_to(node: "Node") -> "Param"
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/designer/base.py#L58)

Attach the param to the node.

**Arguments**:

- `node`: the node

**Returns**:

the param

#### link

```python
def link(to_param: "Param") -> "Param"
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/designer/base.py#L75)

Link the output of the param to the input of another param.

**Arguments**:

- `to_param`: the input param

**Returns**:

the param

#### back\_link

```python
def back_link(from_param: "Param") -> "Param"
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/designer/base.py#L86)

Link the input of the param to the output of another param.

**Arguments**:

- `from_param`: the output param

**Returns**:

the param

### Link Objects

```python
class Link(Serializable)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/designer/base.py#L121)

Link class, this class will be used to link the output of the node to the
input of another node.

#### attach\_to

```python
def attach_to(pipeline: "DesignerPipeline")
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/designer/base.py#L204)

Attach the link to the pipeline.

**Arguments**:

- `pipeline`: the pipeline

### ParamProxy Objects

```python
class ParamProxy(Serializable)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/designer/base.py#L236)

#### special\_prompt\_handling

```python
def special_prompt_handling(code: str, value: str) -> None
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/designer/base.py#L285)

This method will handle the special prompt handling for asset nodes
having `text-generation` function type.

### Node Objects

```python
class Node(Generic[TI, TO], Serializable)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/designer/base.py#L357)

Node class is the base class for all the nodes in the pipeline. This class
will be used to create the nodes and link them together.

#### attach\_to

```python
def attach_to(pipeline: "DesignerPipeline")
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/designer/base.py#L390)

Attach the node to the pipeline.

**Arguments**:

- `pipeline`: the pipeline

