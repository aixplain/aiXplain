---
sidebar_label: model_with_params
title: aixplain.v1.modules.agent.model_with_params
---

فئة عامة تُغلِّف نموذجًا بمعاملات إضافية.

هذه فئة أساسية مجردة يجب توسيعها بواسطة مُغلِّفات نماذج محددة.

مثال على الاستخدام:

class MyModel(ModelWithParams):
    model_id: Text = &quot;my_model&quot;
    extra_param: int = 10

    @field_validator(&quot;extra_param&quot;)
    def validate_extra_param(cls, v: int) -&gt; int:
        if v &lt; 0:
            raise ValueError(&quot;Extra parameter must be positive&quot;)
        return v

### كائنات ModelWithParams

```python
class ModelWithParams(BaseModel, ABC)
```

<!-- ملاحظات الترجمة: [ترجمة "A generic class" إلى "فئة عامة" وفق المسرد] | [ترجمة "model wrappers" إلى "مُغلِّفات نماذج" للوضوح التقني] | [kept EN: ModelWithParams, BaseModel, ABC — أسماء فئات برمجية] | [kept EN: sidebar_label, title — بيانات وصفية للنظام] -->