---
sidebar_label: client
title: aixplain.v2.client
---

وحدة العميل لإجراء طلبات HTTP إلى واجهة API الخاصة بـ aiXplain.

#### create\_retry\_session

```python
def create_retry_session(total: Optional[int] = None,
                         backoff_factor: Optional[float] = None,
                         status_forcelist: Optional[List[int]] = None,
                         **kwargs: Any) -> requests.Session
```

<!-- ملاحظات الترجمة: [تُرجمت "Client module" إلى "وحدة العميل"] | [تُرجمت "HTTP requests" إلى "طلبات HTTP"] | [kept EN: API — brand/technical acronym] | [kept EN: aiXplain — brand name] | [kept EN: create_retry_session — function name] | [الكود لم يُترجم حسب التعليمات] -->