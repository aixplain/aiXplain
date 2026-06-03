---
sidebar_label: sql_tool
title: aixplain.modules.agent.tool.sql_tool
---

أداة SQL لوكلاء aiXplain SDK.

توفر هذه الوحدة أداة تتيح للوكلاء تنفيذ استعلامات SQL
على قواعد البيانات وملفات CSV.

حقوق النشر 2024 لمؤلفي aiXplain SDK

مرخّص بموجب رخصة Apache، الإصدار 2.0 ("الرخصة")؛
لا يجوز لك استخدام هذا الملف إلا وفقًا للرخصة.
يمكنك الحصول على نسخة من الرخصة على:

     http://www.apache.org/licenses/LICENSE-2.0

ما لم يكن مطلوبًا بموجب القانون المعمول به أو تم الاتفاق عليه كتابيًا، يتم توزيع البرنامج
بموجب هذه الرخصة على أساس "كما هو"،
دون أي ضمانات أو شروط من أي نوع، صريحة كانت أو ضمنية.
راجع الرخصة للاطلاع على الأذونات والقيود المحددة
بموجب الرخصة.

المؤلف: Lucas Pavanelli و Thiago Castro Ferreira
التاريخ: 16 مايو 2024
الوصف:
    فئة التوكيل (Agentification)

### كائنات SQLToolError

```python
class SQLToolError(Exception)
```

<!-- ملاحظات الترجمة: [استخدام "أداة" لـ Tool وفق المسرد] | [استخدام "وكلاء" لـ agents وفق المسرد] | [استخدام "استعلامات" لـ queries وفق المسرد] | [kept EN: SQL — اسم لغة برمجة] | [kept EN: CSV — اختصار تقني] | [kept EN: Apache License — اسم رخصة] | [kept EN: Lucas Pavanelli, Thiago Castro Ferreira — أسماء مؤلفين] | [ترجمة Agentification مع إبقاء المصطلح الأصلي بين قوسين للوضوح] -->