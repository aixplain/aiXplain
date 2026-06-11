---
sidebar_label: model_factory_cli
title: aixplain.factories.cli.model_factory_cli
---

#### \_\_author\_\_

حقوق النشر 2022 لمؤلفي aiXplain SDK

مرخَّص بموجب رخصة Apache، الإصدار 2.0 ("الرخصة")؛
لا يجوز لك استخدام هذا الملف إلا وفقًا للرخصة.
يمكنك الحصول على نسخة من الرخصة على:

     http://www.apache.org/licenses/LICENSE-2.0

ما لم يكن مطلوبًا بموجب القانون المعمول به أو متفقًا عليه كتابيًا، يتم توزيع البرنامج
بموجب هذه الرخصة على أساس "كما هو" دون أي ضمانات أو شروط من أي نوع،
سواء كانت صريحة أو ضمنية.
راجع الرخصة للاطلاع على الأذونات والقيود المحددة بموجبها.

المؤلف: Michael Lam
التاريخ: 18 سبتمبر 2023
الوصف:
    واجهة سطر أوامر مصنع النماذج

#### list\_host\_machines

```python
@click.command("hosts")
@click.option("--api-key",
              default=None,
              help="TEAM_API_KEY if not already set in environment")
def list_host_machines(api_key: Optional[Text] = None) -> None
```

<!-- ملاحظات الترجمة: أُبقي على sidebar_label وtitle كمعرّفات تقنية | أُبقي على اسم المؤلف Michael Lam كما هو | kept EN: CLI — اختصار تقني معياري | kept EN: Apache License — اسم رخصة رسمي | أُبقي على كتلة الشيفرة البرمجية دون ترجمة | Model Factory CLI تُرجم إلى "واجهة سطر أوامر مصنع النماذج" -->