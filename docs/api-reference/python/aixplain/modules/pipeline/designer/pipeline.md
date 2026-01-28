---
sidebar_label: pipeline
title: aixplain.modules.pipeline.designer.pipeline
---

### DesignerPipeline Objects

```python
class DesignerPipeline(Serializable)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/designer/pipeline.py#L26)

#### add\_node

```python
def add_node(node: Node)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/designer/pipeline.py#L35)

Add a node to the current pipeline.

This method will take care of setting the pipeline instance to the
node and setting the node number if it&#x27;s not set.

**Arguments**:

- `node`: the node

**Returns**:

the node

#### add\_nodes

```python
def add_nodes(*nodes: Node) -> List[Node]
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/designer/pipeline.py#L47)

Add multiple nodes to the current pipeline.

**Arguments**:

- `nodes`: the nodes

**Returns**:

the nodes

#### add\_link

```python
def add_link(link: Link) -> Link
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/designer/pipeline.py#L56)

Add a link to the current pipeline.

**Arguments**:

- `link`: the link

**Returns**:

the link

#### serialize

```python
def serialize() -> dict
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/designer/pipeline.py#L64)

Serialize the pipeline to a dictionary. This method will serialize the

pipeline to a dictionary.

**Returns**:

the pipeline as a dictionary

#### validate\_nodes

```python
def validate_nodes()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/designer/pipeline.py#L89)

Validate the linkage of the pipeline. This method will validate the

linkage of the pipeline by applying the following checks:
- All input nodes are linked out
- All output nodes are linked in
- All other nodes are linked in and out

**Raises**:

- `ValueError`: if the pipeline is not valid

#### is\_param\_linked

```python
def is_param_linked(node, param)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/designer/pipeline.py#L129)

Check if the param is linked to another node. This method will check

if the param is linked to another node.

**Arguments**:

- `node`: the node
- `param`: the param

**Returns**:

True if the param is linked, False otherwise

#### is\_param\_set

```python
def is_param_set(node, param)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/designer/pipeline.py#L143)

Check if the param is set. This method will check if the param is set

or linked to another node.

**Arguments**:

- `node`: the node
- `param`: the param

**Returns**:

True if the param is set, False otherwise

#### special\_prompt\_validation

```python
def special_prompt_validation(node: Node)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/designer/pipeline.py#L153)

This method will handle the special rule for asset nodes having

`text-generation` function type where if any prompt variable exists
then the `text` param is not required but the prompt param are.

**Arguments**:

- `node`: the node

**Raises**:

- `ValueError`: if the pipeline is not valid

#### validate\_params

```python
def validate_params()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/designer/pipeline.py#L171)

This method will check if all required params are either set or linked

**Raises**:

- `ValueError`: if the pipeline is not valid

#### validate

```python
def validate()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/designer/pipeline.py#L183)

Validate the pipeline. This method will validate the pipeline by

series of checks:
- Validate all nodes are linked correctly
- Validate all required params are set or linked

Any other validation checks can be added here.

**Raises**:

- `ValueError`: if the pipeline is not valid

#### get\_link

```python
def get_link(from_node: int, to_node: int) -> Link
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/designer/pipeline.py#L197)

Get the link between two nodes. This method will return the link

between two nodes.

**Arguments**:

- `from_node`: the from node number
- `to_node`: the to node number

**Returns**:

the link

#### get\_node

```python
def get_node(node_number: int) -> Node
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/designer/pipeline.py#L211)

Get the node by its number. This method will return the node with the

given number.

**Arguments**:

- `node_number`: the node number

**Returns**:

the node

#### auto\_infer

```python
def auto_infer()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/designer/pipeline.py#L221)

Automatically infer the data types of the nodes in the pipeline.
This method will automatically infer the data types of the nodes in the
pipeline by traversing the pipeline and setting the data types of the
nodes based on the data types of the connected nodes.

#### asset

```python
def asset(asset_id: str,
          *args,
          asset_class: Type[T] = AssetNode,
          **kwargs) -> T
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/designer/pipeline.py#L231)

Shortcut to create an asset node for the current pipeline.

All params will be passed as keyword arguments to the node
constructor.

**Arguments**:

- `kwargs`: keyword arguments

**Returns**:

the node

#### utility

```python
def utility(asset_id: str,
            *args,
            asset_class: Type[T] = Utility,
            **kwargs) -> T
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/designer/pipeline.py#L242)

Shortcut to create an utility nodes for the current pipeline.

All params will be passed as keyword arguments to the node
constructor.

**Arguments**:

- `kwargs`: keyword arguments

**Returns**:

the node

#### decision

```python
def decision(*args, **kwargs) -> Decision
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/designer/pipeline.py#L256)

Shortcut to create an decision node for the current pipeline.

All params will be passed as keyword arguments to the node
constructor.

**Arguments**:

- `kwargs`: keyword arguments

**Returns**:

the node

#### script

```python
def script(*args, **kwargs) -> Script
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/designer/pipeline.py#L267)

Shortcut to create an script node for the current pipeline.

All params will be passed as keyword arguments to the node
constructor.

**Arguments**:

- `kwargs`: keyword arguments

**Returns**:

the node

#### input

```python
def input(*args, **kwargs) -> Input
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/designer/pipeline.py#L278)

Shortcut to create an input node for the current pipeline.

All params will be passed as keyword arguments to the node
constructor.

**Arguments**:

- `kwargs`: keyword arguments

**Returns**:

the node

#### output

```python
def output(*args, **kwargs) -> Output
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/designer/pipeline.py#L289)

Shortcut to create an output node for the current pipeline.

All params will be passed as keyword arguments to the node
constructor.

**Arguments**:

- `kwargs`: keyword arguments

**Returns**:

the node

#### router

```python
def router(routes: Tuple[DataType, Node], *args, **kwargs) -> Router
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/designer/pipeline.py#L300)

Shortcut to create an decision node for the current pipeline.

All params will be passed as keyword arguments to the node
constructor. The routes will be handled specially and will be
converted to Route instances in a convenient way.

**Arguments**:

- `routes`: the routes
- `kwargs`: keyword arguments

**Returns**:

the node

#### bare\_reconstructor

```python
def bare_reconstructor(*args, **kwargs) -> BareReconstructor
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/designer/pipeline.py#L322)

Shortcut to create an reconstructor node for the current pipeline.

All params will be passed as keyword arguments to the node
constructor.

**Arguments**:

- `kwargs`: keyword arguments

**Returns**:

the node

#### bare\_segmentor

```python
def bare_segmentor(*args, **kwargs) -> BareSegmentor
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/designer/pipeline.py#L333)

Shortcut to create an segmentor node for the current pipeline.

All params will be passed as keyword arguments to the node
constructor.

**Arguments**:

- `kwargs`: keyword arguments

**Returns**:

the node

#### metric

```python
def metric(*args, **kwargs) -> BareMetric
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/designer/pipeline.py#L344)

Shortcut to create an metric node for the current pipeline.

All params will be passed as keyword arguments to the node
constructor.

**Arguments**:

- `kwargs`: keyword arguments

**Returns**:

the node

