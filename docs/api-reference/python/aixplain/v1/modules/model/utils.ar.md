---
sidebar_label: utils
title: aixplain.v1.modules.model.utils
---

دوال مساعدة لعمليات النموذج تشمل بناء الحمولة وتحليل الشيفرة البرمجية.

توفر هذه الوحدة دوال مساعدة لبناء حمولات API، وتحليل الشيفرة البرمجية للنماذج المساعدة،
ومعالجة نقاط النهاية الخاصة بتنفيذ النموذج.

#### build\_payload

```python
def build_payload(data: Union[Text, Dict],
                  parameters: Optional[Dict] = None,
                  stream: Optional[bool] = None)
```

<!-- ملاحظات الترجمة: [utility functions → دوال مساعدة للتوافق مع السياق التقني] | [payload building → بناء الحمولة حسب المسرد] | [code parsing → تحليل الشيفرة البرمجية] | [kept EN: API — اختصار تقني معتمد] | [kept EN: build_payload — اسم دالة لا يُترجم] -->