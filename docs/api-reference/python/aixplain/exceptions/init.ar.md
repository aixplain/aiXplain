---
sidebar_label: exceptions
title: aixplain.exceptions
---

سجل رسائل الخطأ لحزمة aiXplain SDK.

تحتفظ هذه الوحدة بسجل مركزي لرسائل الخطأ المستخدمة في جميع أنحاء منظومة aiXplain.
وتتيح للمطورين البحث عن رسائل الخطأ الموجودة وإعادة استخدامها بدلاً من إنشاء رسائل جديدة.

#### get\_error\_from\_status\_code

```python
def get_error_from_status_code(status_code: int,
                               error_details: str = None
                               ) -> AixplainBaseException
```

<!-- ملاحظات الترجمة: [أُبقي على sidebar_label وtitle كقيم تهيئة دون ترجمة] | [أُبقي على اسم الدالة get_error_from_status_code وكتلة الشيفرة دون ترجمة] | [kept EN: aiXplain — brand name] | [kept EN: SDK — technical acronym] -->