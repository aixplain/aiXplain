---
sidebar_label: model_factory_cli
title: aixplain.v1.factories.cli.model_factory_cli
---

#### \_\_author\_\_

حقوق النشر 2022 لمؤلفي aiXplain SDK

مرخّص بموجب رخصة Apache، الإصدار 2.0 (&quot;الرخصة&quot;)؛
لا يجوز لك استخدام هذا الملف إلا وفقًا للرخصة.
يمكنك الحصول على نسخة من الرخصة على:

     http://www.apache.org/licenses/LICENSE-2.0

ما لم يكن مطلوبًا بموجب القانون المعمول به أو متفقًا عليه كتابيًا، يتم توزيع البرنامج
بموجب الرخصة على أساس &quot;كما هو&quot; (AS IS)،
دون أي ضمانات أو شروط من أي نوع، سواء كانت صريحة أو ضمنية.
راجع الرخصة للاطلاع على الأذونات والقيود المحددة
بموجب الرخصة.

المؤلف: Michael Lam
التاريخ: 18 سبتمبر 2023
الوصف:
    واجهة سطر الأوامر لمصنع النماذج

#### list\_host\_machines

```python
@click.command("hosts")
@click.option("--api-key",
              default=None,
              help="TEAM_API_KEY if not already set in environment")
def list_host_machines(api_key: Optional[Text] = None) -> None
```

<!-- ملاحظات الترجمة: [أُبقي على sidebar_label وtitle كمسارات وحدات برمجية دون ترجمة] | [أُبقي على اسم الدالة list_host_machines دون ترجمة] | [kept EN: aiXplain SDK — brand name] | [kept EN: Apache License — proper noun] | [kept EN: Michael Lam — author name] | [لم يُترجم محتوى كتلة الشيفرة البرمجية] | [تُرجم Model Factory CLI إلى "واجهة سطر الأوامر لمصنع النماذج" وفق مصطلح النماذج من المسرد] -->