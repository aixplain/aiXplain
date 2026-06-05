---
sidebar_label: model_tool
title: aixplain.modules.agent.tool.model_tool
---

أداة النموذج لوكلاء aiXplain SDK.

توفر هذه الوحدة أداة تتيح للوكلاء التفاعل مع نماذج الذكاء الاصطناعي
وتنفيذ المهام المبنية على النماذج.

حقوق النشر 2024 لمؤلفي aiXplain SDK

مرخص بموجب رخصة Apache، الإصدار 2.0 ("الرخصة")؛
لا يجوز لك استخدام هذا الملف إلا وفقًا للرخصة.
يمكنك الحصول على نسخة من الرخصة على:

     http://www.apache.org/licenses/LICENSE-2.0

ما لم يكن مطلوبًا بموجب القانون المعمول به أو تم الاتفاق عليه كتابيًا، يتم توزيع البرنامج
بموجب هذه الرخصة على أساس "كما هو"،
دون أي ضمانات أو شروط من أي نوع، صريحة كانت أو ضمنية.
راجع الرخصة للاطلاع على الأذونات والقيود المحددة
المنصوص عليها في الرخصة.

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

<!-- ملاحظات الترجمة: [Agentification ترجمت وصفيًا مع إبقاء المصطلح الأصلي بين قوسين لعدم وجوده في المسرد] | [kept EN: aiXplain, SDK — brand names] | [kept EN: Apache License — proper noun] | [kept EN: author names — policy] | [kept EN: code block — never translate] -->