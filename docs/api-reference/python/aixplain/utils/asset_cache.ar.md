---
sidebar_label: asset_cache
title: aixplain.utils.asset_cache
---

وحدة أداة ذاكرة مؤقتة للأصول في aiXplain SDK.

توفر هذه الوحدة نظام تخزين مؤقت عام لأصول aiXplain (النماذج، وخطوط المعالجة،
والوكلاء، وغيرها) مع استمرارية قائمة على الملفات، وتسلسل تلقائي، وانتهاء صلاحية،
وعمليات آمنة لتعدد الخيوط.

### كائنات Store

```python
@dataclass
class Store(Generic[T])
```

<!-- ملاحظات الترجمة: [Models→النماذج حسب المسرد] | [Pipelines→خطوط المعالجة حسب المسرد] | [Agents→الوكلاء حسب المسرد] | [kept EN: aiXplain SDK — brand name] | [kept EN: Store, Generic[T], @dataclass — code identifiers] -->