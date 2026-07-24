---
sidebar_label: skill
title: aixplain.v2.skill
---

Skill resource module.

A ``Skill`` is a Claude-style skill — a ``SKILL.md`` (YAML frontmatter + markdown
instructions), optionally alongside ``scripts/`` and ``resources/`` — registered as
an aiXplain asset and attachable to agents. It is authored from a local path, either
a folder containing ``SKILL.md`` or a single ``.md`` file; the file tree is uploaded
and managed internally.

The frontmatter ``description`` is the routing signal an agent sees; the body and
resources are loaded just-in-time at runtime (progressive disclosure). Skills are
attached to agents the same way tools are::

    skill = aix.Skill(file_path=&quot;./skills/pdf-filler&quot;)  # folder
    skill = aix.Skill(file_path=&quot;calculator.md&quot;)        # single file
    skill.save()                                   # upload bundle + register asset

    agent = aix.Agent(name=&quot;analyst&quot;, skills=[skill])
    agent.save()

    aix.Skill.get(&quot;my-workspace/pdf-filler&quot;)       # retrieve (path or id)
    aix.Skill.search(&quot;pdf form&quot;)                   # search
    skill.download()                               # download the bundle to ./\{name}.zip
    skill.download(file_path=&quot;./pdf-filler.zip&quot;)   # ...or an explicit path

### SkillSearchParams Objects

```python
class SkillSearchParams(BaseSearchParams)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/skill.py#L78)

Search parameters for skills.

**Attributes**:

- `tags` - Filter by tags.
- `suppliers` - Filter by suppliers.
- `saved` - Only return skills the caller has saved.

### Skill Objects

```python
@dataclass_json

@dataclass(repr=False)
class Skill(BaseResource, SearchResourceMixin[SkillSearchParams, "Skill"],
            GetResourceMixin[BaseGetParams, "Skill"],
            DeleteResourceMixin[BaseDeleteParams, "Skill"], ToolableMixin)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/skill.py#L94)

A Claude-style skill registered as an aiXplain asset.

Authored from a local path via ``aix.Skill(file_path=...)`` — either a folder
containing ``SKILL.md`` or a single ``.md`` file; the bundle&#x27;s file tree is
uploaded internally on ``save()``. Attach to agents with
``aix.Agent(skills=[skill_or_id])``.

#### \_\_post\_init\_\_

```python
def __post_init__() -> None
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/skill.py#L133)

Load skill metadata from the local path when authoring a new skill.

#### get

```python
@classmethod
def get(cls: type["Skill"], id: str,
        **kwargs: Unpack[BaseGetParams]) -> "Skill"
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/skill.py#L174)

Get a skill by path or id.

#### search

```python
@classmethod
def search(cls: type["Skill"],
           query: Optional[str] = None,
           **kwargs: Unpack[SkillSearchParams]) -> Page["Skill"]
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/skill.py#L179)

Search skills with an optional free-text query and filters.

#### save

```python
def save(*args: Any, **kwargs: Any) -> "Skill"
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/skill.py#L204)

Save the skill, uploading the bundle when authored from a local path.

**Arguments**:

- `*args` - Positional arguments passed to the base save method.
- `**kwargs` - Attributes to set before saving (passed to base save).

#### refresh

```python
def refresh() -> "Skill"
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/skill.py#L220)

Reload the skill&#x27;s metadata from the backend.

#### download

```python
def download(file_path: Optional[str] = None) -> str
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/skill.py#L227)

Download the skill bundle to a local path. Returns the written path.

**Arguments**:

- `file_path` - Where to write the bundle. Defaults to ``./\{name}.zip``.

#### as\_tool

```python
def as_tool() -> dict
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/skill.py#L241)

Serialize this skill as a tool object for agent attachment.

Skills follow the same wire design as tools: attached as objects (not bare
ids), with ``type=&quot;skill&quot;``.

