---
sidebar_label: utils
title: aixplain.factories.pipeline_factory.utils
---

#### build\_from\_response

```python
def build_from_response(response: Dict,
                        load_architecture: bool = False) -> Pipeline
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/factories/pipeline_factory/utils.py#L23)

Convert API response into a Pipeline object.

This function creates a Pipeline object from an API response, optionally loading
its full architecture including nodes and links. The architecture can include
various node types like Input, Output, BareAsset, BareMetric, Decision, Router,
Script, BareSegmentor, and BareReconstructor.

**Arguments**:

- `response` _Dict_ - API response containing pipeline information including:
  - id: Pipeline identifier
  - name: Pipeline name
  - api_key: Optional API key
  - status: Pipeline status (defaults to &quot;draft&quot;)
  - nodes: Optional list of node configurations
  - links: Optional list of link configurations
- `load_architecture` _bool, optional_ - Whether to load the full pipeline
  architecture including nodes and links. Defaults to False.
  

**Returns**:

- `Pipeline` - Instantiated pipeline object. If load_architecture is True,
  includes all configured nodes and links. If architecture loading fails,
  returns a pipeline with empty nodes and links lists.
  

**Notes**:

  When loading architecture, decision nodes with passthrough parameters are
  processed first to ensure proper parameter linking.

