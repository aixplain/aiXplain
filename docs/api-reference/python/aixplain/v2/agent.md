---
sidebar_label: agent
title: aixplain.v2.agent
---

### Agent Objects

```python
class Agent(BaseResource, ListResourceMixin[BareListParams, "Agent"],
            GetResourceMixin[BareGetParams, "Agent"])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/agent.py#L45)

Resource for agents.

**Attributes**:

- `RESOURCE_PATH` - str: The resource path.
- `PAGINATE_PATH` - None: The path for pagination.
- `PAGINATE_METHOD` - str: The method for pagination.
- `PAGINATE_ITEMS_KEY` - None: The key for the response.

#### create\_pipeline\_tool

```python
@classmethod
def create_pipeline_tool(cls,
                         description: str,
                         pipeline: Union["Pipeline", str],
                         name: Optional[str] = None) -> "PipelineTool"
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/agent.py#L107)

Create a new pipeline tool.

#### create\_python\_interpreter\_tool

```python
@classmethod
def create_python_interpreter_tool(cls) -> "PythonInterpreterTool"
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/agent.py#L116)

Create a new python interpreter tool.

#### create\_custom\_python\_code\_tool

```python
@classmethod
def create_custom_python_code_tool(
        cls,
        code: Union[str, Callable],
        name: str,
        description: str = "") -> "ConnectionTool"
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/agent.py#L123)

Create a new custom python code tool.

#### create\_sql\_tool

```python
@classmethod
def create_sql_tool(cls,
                    name: str,
                    description: str,
                    source: str,
                    source_type: str,
                    schema: Optional[str] = None,
                    tables: Optional[List[str]] = None,
                    enable_commit: bool = False) -> "SQLTool"
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/agent.py#L132)

Create a new SQL tool.

**Arguments**:

- `description` _str_ - description of the database tool
- `source` _Union[str, Dict]_ - database source - can be a connection string or dictionary with connection details
- `source_type` _str_ - type of source (sqlite, csv)
- `schema` _Optional[str], optional_ - database schema description
- `tables` _Optional[List[str]], optional_ - table names to work with (optional)
- `enable_commit` _bool, optional_ - enable to modify the database (optional)
  

**Returns**:

- `SQLTool` - created SQLTool
  

**Examples**:

  # SQLite - Simple
  sql_tool = Agent.create_sql_tool(
  description=&quot;My SQLite Tool&quot;,
  source=&quot;/path/to/database.sqlite&quot;,
  source_type=&quot;sqlite&quot;,
  tables=[&quot;users&quot;, &quot;products&quot;]
  )
  
  # CSV - Simple
  sql_tool = Agent.create_sql_tool(
  description=&quot;My CSV Tool&quot;,
  source=&quot;/path/to/data.csv&quot;,
  source_type=&quot;csv&quot;,
  tables=[&quot;data&quot;]
  )

