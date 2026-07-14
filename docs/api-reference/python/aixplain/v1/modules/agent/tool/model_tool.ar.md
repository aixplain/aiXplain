---
sidebar_label: model_tool
title: aixplain.v1.modules.agent.tool.model_tool
---

أداة النموذج لوكلاء aiXplain SDK.

توفر هذه الوحدة أداة تتيح للوكلاء التفاعل مع نماذج الذكاء الاصطناعي
وتنفيذ المهام المستندة إلى النماذج.

حقوق النشر 2024 لمؤلفي aiXplain SDK

مرخّص بموجب رخصة Apache، الإصدار 2.0 ("الرخصة")؛
لا يجوز لك استخدام هذا الملف إلا وفقًا للرخصة.
يمكنك الحصول على نسخة من الرخصة على:

     http://www.apache.org/licenses/LICENSE-2.0

ما لم يكن مطلوبًا بموجب القانون المعمول به أو متفقًا عليه كتابيًا، يُوزَّع البرنامج
بموجب الرخصة على أساس "كما هو"،
دون أي ضمانات أو شروط من أي نوع، سواء كانت صريحة أو ضمنية.
راجع الرخصة للاطلاع على الأذونات والقيود المحددة
بموجب الرخصة.

المؤلف: Lucas Pavanelli و Thiago Castro Ferreira
التاريخ: 16 مايو 2024
الوصف:
    فئة التوكيل (Agentification)

#### set\_tool\_name

```python
def set_tool_name(function: Function,
                  supplier: Supplier = None,
                  model: Model = None) -> Text
```

<!-- ملاحظات الترجمة: [ترجمة "Model tool" إلى "أداة النموذج" وفق المسرد] | [ترجمة "module" إلى "وحدة" وفق المسرد] | [kept EN: aiXplain SDK — brand name] | [kept EN: Apache License — proper noun] | [kept EN: Lucas Pavanelli, Thiago Castro Ferreira — author names] | [kept EN: code block — never translated] | [ترجمة "Agentification Class" مع إبقاء المصطلح الإنجليزي بين قوسين للوضوح] -->