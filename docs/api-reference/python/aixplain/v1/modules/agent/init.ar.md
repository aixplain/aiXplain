---
sidebar_label: agent
title: aixplain.v1.modules.agent
---

وحدة الوكيل لـ aiXplain SDK.

توفر هذه الوحدة فئة Agent والوظائف المرتبطة بها لإنشاء وإدارة
الوكلاء الذكيين القادرين على تنفيذ المهام باستخدام أدوات ونماذج متنوعة.

حقوق النشر 2024 لمؤلفي aiXplain SDK

مرخَّص بموجب رخصة Apache، الإصدار 2.0 ("الرخصة")؛
لا يجوز لك استخدام هذا الملف إلا وفقًا للرخصة.
يمكنك الحصول على نسخة من الرخصة على:

     http://www.apache.org/licenses/LICENSE-2.0

ما لم يكن مطلوبًا بموجب القانون المعمول به أو متفقًا عليه كتابيًا، يُوزَّع البرنامج
بموجب الرخصة على أساس "كما هو"،
دون أي ضمانات أو شروط من أي نوع، صريحة كانت أو ضمنية.
راجع الرخصة للاطلاع على الأذونات والقيود المحددة
بموجب الرخصة.

المؤلف: Lucas Pavanelli و Thiago Castro Ferreira
التاريخ: 16 مايو 2024
الوصف:
    فئة الوكيل (Agentification)

### كائنات Agent

```python
class Agent(Model, DeployableMixin[Union[Tool, DeployableTool]])
```

<!-- ملاحظات الترجمة: أُبقي على sidebar_label وtitle كما هما لأنهما معرّفات تقنية | أُبقي على أسماء المؤلفين بالإنجليزية | kept EN: Agent — اسم فئة برمجية | kept EN: Agentification — مصطلح تقني خاص بالوصف الأصلي | kept EN: Model, DeployableMixin, Tool, DeployableTool — أسماء فئات برمجية داخل كتلة شيفرة -->