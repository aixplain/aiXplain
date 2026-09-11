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

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/skill.py#L80)

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

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/skill.py#L96)

A Claude-style skill registered as an aiXplain asset.

Authored from a local path via ``aix.Skill(file_path=...)`` — either a folder
containing ``SKILL.md`` or a single ``.md`` file; the bundle&#x27;s file tree is
uploaded internally on ``save()``. Attach to agents with
``aix.Agent(skills=[skill_or_id])``.

#### \_\_post\_init\_\_

```python
def __post_init__() -> None
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/skill.py#L135)

Load skill metadata from the local path when authoring a new skill.

#### get

```python
@classmethod
def get(cls: type["Skill"], id: str,
        **kwargs: Unpack[BaseGetParams]) -> "Skill"
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/skill.py#L221)

Get a skill by path or id.

#### search

```python
@classmethod
def search(cls: type["Skill"],
           query: Optional[str] = None,
           **kwargs: Unpack[SkillSearchParams]) -> Page["Skill"]
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/skill.py#L226)

Search skills with an optional free-text query and filters.

#### save

```python
def save(*args: Any, **kwargs: Any) -> "Skill"
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/skill.py#L251)

Save the skill, uploading the bundle when authored from a local path.

Re-parses ``file_path`` from disk on every call, so re-saving an already
saved ``Skill`` after editing its ``SKILL.md`` (or reassigning
``file_path`` to updated content) re-uploads the bundle — and picks up an
edited frontmatter ``name``/``description`` — instead of silently
skipping it. The uploaded tree is added to and updated in place: a file
deleted or renamed locally is *not* removed from the bundle.

**Arguments**:

- ``2 - Positional arguments passed to the base save method.
- ``3 - Attributes to set before saving (passed to base save).
  

**Raises**:

- ``4 - If the skill has been deleted — the same type every
  other deleted-save guard raises (BUG-1093), which is why the
  guard runs before this method touches the disk.

#### refresh

```python
def refresh() -> "Skill"
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/skill.py#L287)

Reload the skill&#x27;s metadata from the backend.

#### download

```python
def download(file_path: Optional[str] = None) -> str
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/skill.py#L294)

Download the skill bundle to a local path. Returns the written path.

**Arguments**:

- `file_path` - Where to write the bundle. Defaults to ``./\{name}.zip``.

#### list\_files

```python
def list_files() -> List[str]
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/skill.py#L308)

List the relative paths of every file and folder in this skill&#x27;s bundle.

Use this to find the ``name`` to pass to :meth:`update` when you want
to swap out an existing file (or add a new one) with local content —
e.g. ``&quot;SKILL.md&quot;``, ``&quot;scripts/helper.py&quot;``, ``&quot;resources&quot;``.

#### as\_tool

```python
def as_tool() -> dict
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/skill.py#L317)

Serialize this skill as a tool object for agent attachment.

Skills follow the same wire design as tools: attached as objects (not bare
ids), with ``type=&quot;skill&quot;``.

#### update

```python
def update(path: str, name: Optional[str] = None) -> "Skill"
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/skill.py#L424)

Update (or add) a single file or folder within this skill&#x27;s bundle.

Unlike :meth:`save` (which re-uploads every file under ``file_path``),
``update`` pushes just one changed file or subfolder — useful when you
only have the new content on hand, not the original authoring folder. A
node already at ``name`` is updated in place; a new one is created
(intermediate folders are created as needed). Pushing a ``SKILL.md``
also writes its frontmatter ``description`` to the asset.

**Arguments**:

- ``1 - Local file or folder to upload from.
- ``2 - Where this content lives within the skill — a bare filename
  (``&quot;SKILL.md&quot;``) or a relative path (``&quot;scripts/helper.py&quot;``).
  Defaults to ``os.path.basename(path)``.
  

**Returns**:

  This ``Skill``.
  

**Example**:

  &gt;&gt;&gt; skill.update(&quot;./SKILL.md&quot;)                       # replace SKILL.md
  &gt;&gt;&gt; skill.update(&quot;./helper.py&quot;, &quot;scripts/helper.py&quot;)  # add/update a script
  &gt;&gt;&gt; skill.update(&quot;./resources&quot;, &quot;resources&quot;)         # sync a whole subfolder

