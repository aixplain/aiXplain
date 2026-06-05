---
sidebar_label: model_with_params
title: aixplain.modules.agent.model_with_params
---

فئة عامة تغلّف نموذجًا بمعاملات إضافية.

هذه فئة أساسية مجردة يجب توسيعها بواسطة أغلفة نماذج محددة.

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

<!-- ملاحظات الترجمة: ["generic class" ترجمت إلى "فئة عامة"] | ["abstract base class" ترجمت إلى "فئة أساسية مجردة"] | ["model wrappers" ترجمت إلى "أغلفة نماذج"] | [kept EN: ModelWithParams, BaseModel, ABC — أسماء فئات برمجية] | [kept EN: field_validator, ValueError — أسماء دوال/استثناءات برمجية] -->