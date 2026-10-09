---
sidebar_label: skill
title: aixplain.v2.skill
---

`from aixplain import Skill, SkillBatch`


Skill resource module.

A ``Skill`` is a Claude-style skill — a ``SKILL.md`` (YAML frontmatter + markdown
instructions), optionally alongside ``scripts/`` and ``resources/`` — registered as
an aiXplain asset and attachable to agents. It is authored from a local path, either
a folder containing ``SKILL.md`` or a single ``.md`` file; the file tree is uploaded
and managed internally.

The frontmatter ``description`` is the routing signal an agent sees; the body and
resources are loaded just-in-time at runtime (progressive disclosure). Skills are
attached to agents the same way tools are:

```python
skill = aix.Skill(file_path="./skills/pdf-filler")  # folder
skill = aix.Skill(file_path="calculator.md")        # single file
skill.save()                                   # upload bundle + register asset

agent = aix.Agent(name="analyst", skills=[skill])
agent.save()

aix.Skill.get("my-workspace/pdf-filler")       # retrieve (path or id)
aix.Skill.search("pdf form")                   # search
skill.download()                               # download the bundle to ./{name}.zip
skill.download(file_path="./pdf-filler.zip")   # ...or an explicit path
```



### SkillSearchParams Objects

```python
class SkillSearchParams(BaseSearchParams)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/skill.py#L91)

Search parameters for skills.

**Attributes**:

- `tags` - Filter by tags.
- `suppliers` - Filter by suppliers.
- `saved` - Only return skills the caller has saved.

### SkillBatch Objects

```python
@dataclass
class SkillBatch()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/skill.py#L106)

Result of `Skill.get_many`, keyed by the requested id or path.

### Skill Objects

```python
@dataclass_json

@dataclass(repr=False)
class Skill(BaseResource, SearchResourceMixin[SkillSearchParams, "Skill"],
            GetResourceMixin[BaseGetParams, "Skill"],
            DeleteResourceMixin[BaseDeleteParams, "Skill"], ToolableMixin)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/skill.py#L117)

A Claude-style skill registered as an aiXplain asset.

Authored from a local path via ``aix.Skill(file_path=...)`` — either a folder
containing ``SKILL.md`` or a single ``.md`` file; the bundle's file tree is
uploaded internally on ``save()``. Attach to agents with
``aix.Agent(skills=[skill_or_id])``.

#### \_\_post\_init\_\_

```python
def __post_init__() -> None
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/skill.py#L156)

Load skill metadata from the local path when authoring a new skill.

#### get

```python
@classmethod
def get(cls: type["Skill"], id: str,
        **kwargs: Unpack[BaseGetParams]) -> "Skill"
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/skill.py#L242)

Get a skill by path or id.

#### get\_many

```python
@classmethod
def get_many(cls,
             ids: List[str],
             *,
             timeout: Optional[TimeoutType] = None) -> SkillBatch
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/skill.py#L247)

Fetch skills by id, asset path or instance id in batches of at most 100.

**Arguments**:

- `ids` - Skill keys. Duplicates are dropped, order is kept.
- `timeout` - Per-request timeout; the client default applies when omitted.
  

**Returns**:

- `SkillBatch` - Parsed skills and their raw backend rows, keyed by the
  requested key, plus the keys the backend did not find or forbade.
  A row that fails to deserialize is reported in ``not_found``.
  

**Raises**:

- `APIError` - Unchanged from the client on a failed request, so a backend
  without the batch route (404/405) can fall back to per-id ``get``.

#### search

```python
@classmethod
def search(cls: type["Skill"],
           query: Optional[str] = None,
           **kwargs: Unpack[SkillSearchParams]) -> Page["Skill"]
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/skill.py#L293)

Search skills with an optional free-text query and filters.

#### save

```python
def save(*args: Any, **kwargs: Any) -> "Skill"
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/skill.py#L318)

Save the skill, uploading the bundle when authored from a local path.

Re-parses ``file_path`` from disk on every call, so re-saving an already
saved ``Skill`` after editing its ``SKILL.md`` (or reassigning
``file_path`` to updated content) re-uploads the bundle — and picks up an
edited frontmatter ``name``/``description`` — instead of silently
skipping it. The uploaded tree is added to and updated in place: a file
deleted or renamed locally is *not* removed from the bundle.

**Arguments**:

- `*args` - Positional arguments passed to the base save method.
- `**kwargs` - Attributes to set before saving (passed to base save).
  

**Raises**:

- `ResourceError` - If the skill has been deleted — the same type every
  other deleted-save guard raises (BUG-1093), which is why the
  guard runs before this method touches the disk.

#### refresh

```python
def refresh() -> "Skill"
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/skill.py#L354)

Reload the skill's metadata from the backend.

#### download

```python
def download(file_path: Optional[str] = None) -> str
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/skill.py#L361)

Download the skill bundle to a local path. Returns the written path.

**Arguments**:

- `file_path` - Where to write the bundle. Defaults to ``./{name}.zip``.

#### list\_files

```python
def list_files() -> List[str]
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/skill.py#L375)

List the relative paths of every file and folder in this skill's bundle.

Use this to find the ``name`` to pass to `update` when you want
to swap out an existing file (or add a new one) with local content —
e.g. ``"SKILL.md"``, ``"scripts/helper.py"``, ``"resources"``.

#### as\_tool

```python
def as_tool() -> dict
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/skill.py#L384)

Serialize this skill as a tool object for agent attachment.

Skills follow the same wire design as tools: attached as objects (not bare
ids), with ``type="skill"``.

#### update

```python
def update(path: str, name: Optional[str] = None) -> "Skill"
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/skill.py#L491)

Update (or add) a single file or folder within this skill's bundle.

Unlike `save` (which re-uploads every file under ``file_path``),
``update`` pushes just one changed file or subfolder — useful when you
only have the new content on hand, not the original authoring folder. A
node already at ``name`` is updated in place; a new one is created
(intermediate folders are created as needed). Pushing a ``SKILL.md``
also writes its frontmatter ``description`` to the asset.

**Arguments**:

- `path` - Local file or folder to upload from.
- `name` - Where this content lives within the skill — a bare filename
  (``"SKILL.md"``) or a relative path (``"scripts/helper.py"``).
  Defaults to ``os.path.basename(path)``.
  

**Returns**:

  This ``Skill``.
  

**Example**:

  
```python
>>> skill.update("./SKILL.md")                       # replace SKILL.md
>>> skill.update("./helper.py", "scripts/helper.py")  # add/update a script
>>> skill.update("./resources", "resources")         # sync a whole subfolder
```
  
  

