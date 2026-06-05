---
sidebar_label: _compat
title: aixplain._compat
---

مُعيد توجيه الاستيراد المتوافق مع الإصدارات السابقة لإعادة الهيكلة من v1 إلى legacy.

بعد نقل الشيفرة القديمة من مسار مثل ``aixplain/modules/`` إلى
``aixplain/v1/modules/``، تضمن هذه الوحدة أن جميع مسارات الاستيراد الحالية
(``from aixplain.modules import …``، ``from aixplain.factories.model_factory import …``،
إلخ) تستمر في العمل بشفافية عبر مُكتشِف مخصص في ``sys.meta_path``.

يُثبَّت مُعيد التوجيه مرة واحدة أثناء تهيئة الحزمة وتكلفته في وقت التشغيل لا تُذكر
— إذ لا يُفعَّل إلا لمسارات الاستيراد التي تطابق بادئة legacy معروفة.

#### install

```python
def install()
```

<!-- ملاحظات الترجمة: [أُبقي على sidebar_label وtitle كمعرّفات شيفرة] | [أُبقي على مسارات الوحدات وكتل الشيفرة بالإنجليزية] | [kept EN: legacy — technical term referring to old code organization, no standard Arabic equivalent] | [kept EN: sys.meta_path — Python internal API identifier] -->