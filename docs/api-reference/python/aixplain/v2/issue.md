---
sidebar_label: issue
title: aixplain.v2.issue
---

`from aixplain import IssueReporter, IssueSeverity, IssueSeverityValue`


Issue reporting helpers for the V2 SDK.

### IssueSeverity Objects

```python
class IssueSeverity(str, Enum)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/issue.py#L15)

Supported issue severity levels.

#### IssueSeverityValue

The string form of `IssueSeverity`, accepted anywhere the enum is.

### IssueReporter Objects

```python
class IssueReporter()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/issue.py#L28)

submitting SDK issues to the backend.

#### \_\_init\_\_

```python
def __init__(context: "Aixplain") -> None
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/issue.py#L33)

Initialize the issue reporter.

#### report

```python
def report(description: Optional[str],
           *,
           severity: Optional[Union[IssueSeverity, IssueSeverityValue]] = None,
           **kwargs: Any) -> str
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/issue.py#L41)

Submit an issue report and return its ID.

**Arguments**:

- `description` - What went wrong. Required.
- `severity` - ``IssueSeverity`` or its string value ("SEV1".."SEV4").
  Named explicitly rather than left in ``**kwargs`` so a type
  checker can reject a typo against `IssueSeverityValue`.
- `**kwargs` - ``title``, ``tags``, ``sdk_version``, ``runtime_context``
  and ``reporter_email``.

