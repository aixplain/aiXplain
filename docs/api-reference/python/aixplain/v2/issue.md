---
sidebar_label: issue
title: aixplain.v2.issue
---

Issue reporting helpers for the V2 SDK.

### IssueSeverity Objects

```python
class IssueSeverity(str, Enum)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/issue.py#L14)

Supported issue severity levels.

### IssueReporter Objects

```python
class IssueReporter()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/issue.py#L23)

submitting SDK issues to the backend.

#### \_\_init\_\_

```python
def __init__(context: "Aixplain") -> None
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/issue.py#L28)

Initialize the issue reporter.

#### report

```python
def report(description: Optional[str], **kwargs: Any) -> str
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/issue.py#L36)

Submit an issue report and return its ID.

