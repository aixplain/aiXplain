---
sidebar_label: utils
title: aixplain.modules.model.utils
---

دوال مساعدة لعمليات النموذج تشمل بناء الحمولة وتحليل الشيفرة.

توفر هذه الوحدة دوال مساعدة لبناء حمولات API، وتحليل الشيفرة للنماذج المساعدة،
ومعالجة نقاط النهاية الخاصة بتنفيذ النموذج.

#### build\_payload

```python
def build_payload(data: Union[Text, Dict],
                  parameters: Optional[Dict] = None,
                  stream: Optional[bool] = None)
```

<!-- ملاحظات الترجمة: [أُبقي على sidebar_label وtitle كمسارات شيفرة] | [أُبقي على كتلة الكود بالكامل دون ترجمة] | [kept EN: API — اختصار تقني عالمي] | [kept EN: build_payload — اسم دالة] -->