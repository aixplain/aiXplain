---
sidebar_label: actions
title: aixplain.v2.actions
---

تسلسل هرمي موحَّد للإجراءات / المدخلات للنماذج والأدوات.

التسلسل الهرمي للكائنات::

    Actions                    — مجموعة من كائنات Action
      Action                   — بيانات وصفية + يمتلك مدخلاته
        Inputs                 — مجموعة من كائنات Input
          Input                — مدخل فردي بمخطط + قيمة حالية

تمتلك النماذج إجراء &quot;run&quot; ضمني واحد. يتخطى الاختصار ``model.inputs``
طبقة الإجراءات نظرًا لعدم وجود ما يستدعي التمييز.

تمتلك الأدوات إجراءات متعددة، لذا يُستخدم المسار الكامل دائمًا.

### كائنات Input

```python
class Input()
```

<!-- ملاحظات الترجمة: [أُبقيت أسماء الفئات Actions/Action/Inputs/Input بالإنجليزية لأنها معرّفات كود] | [أُبقي sidebar_label وtitle كما هما لأنهما معرّفات تقنية] | [kept EN: run — method name] | [kept EN: model.inputs — code reference] -->