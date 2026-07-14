---
sidebar_label: inspector_factory
title: aixplain.factories.team_agent_factory.inspector_factory
---

وحدة مصنع لإنشاء وتهيئة وكلاء المراقبة.

توفر هذه الوحدة وظائف لإنشاء وكلاء مراقبة قادرين على التحقق من صحة
عمليات وكيل الفريق ومراقبتها. يمكن إنشاء المراقبين من نماذج موجودة
أو باستخدام تهيئات تلقائية.

تحذير: هذه الميزة متاحة حاليًا في الإصدار التجريبي الخاص.

**مثال**:

  إنشاء مراقب من نموذج بسياسة تكيّفية::
  
  inspector = InspectorFactory.create_from_model(
  name=&quot;my_inspector&quot;,
  model_id=&quot;my_model&quot;,
- `model_config=\{"prompt"` - &quot;Check if the data is safe to use.&quot;},
  policy=InspectorPolicy.ADAPTIVE,
  )
  

**ملاحظات**:

  يدعم حاليًا نماذج GUARDRAILS وTEXT_GENERATION فقط كمراقبين.

### كائنات InspectorFactory

```python
class InspectorFactory()
```

<!-- ملاحظات الترجمة: [inspector تُرجمت إلى "مراقب" حسب المسرد المعتمد] | [factory تُرجمت إلى "مصنع" كمصطلح تقني شائع لنمط التصميم] | [kept EN: InspectorFactory, InspectorPolicy, GUARDRAILS, TEXT_GENERATION, create_from_model — أسماء فئات/طرق/قيم ثوابت برمجية] | [kept EN: ADAPTIVE — قيمة enum] -->