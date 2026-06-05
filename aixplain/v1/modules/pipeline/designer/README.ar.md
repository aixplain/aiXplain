# دليل مستخدم Aixplan SDK

## المقدمة

يوفر Aixplan SDK واجهة برمجية (API) لإنشاء خطوط معالجة لبناء الحلول على منصة Aixplain.

## مثال مبسّط

إليك مثالًا سريعًا للبدء:

```python
from aixplain.factories.pipeline_factory import PipelineFactory

TRANSLATION_ASSET_ID = 'your-translation-asset-id'

pipeline = PipelineFactory.init('Translation Pipeline')
input_node = pipeline.input()
translation_node = pipeline.translation(assetId=TRANSLATION_ASSET_ID)

input_node.link(translation_node, 'input', 'text')

output_node = translation_node.use_output('data')

pipeline.save()
outputs = pipeline.run('This is example text to translate')

print(outputs)
```

## إنشاء العُقد

لإنشاء خط معالجة وإنشاء العُقد، استخدم الكود التالي:

```python
from aixplain.factories.pipeline_factory import PipelineFactory
from aixplain.modules.pipeline.designer import Input

pipeline = PipelineFactory.init("My Pipeline")
input_node = Input(*args, **kwargs)
input_node.attach(pipeline)
```

بدلاً من ذلك، أضف العُقد إلى خط المعالجة باستخدام `add_node`:

```python
input_node = pipeline.add_node(Input(*args, **kwargs))
```

يمكنك أيضًا تمرير خط المعالجة إلى مُنشئ العُقدة:

```python
input_node = Input(*args, pipeline=pipeline, **kwargs)
```

أو إنشاء العُقدة مباشرةً ضمن خط المعالجة:

```python
input_node = pipeline.input(*args, **kwargs)
```

## إضافة عُقد المخرجات

يجب أن يحتوي كل خط معالجة على عُقدة مدخل واحدة على الأقل، وعُقدة أصل، وعُقدة مخرج. أضف عُقد المخرجات كأي عُقدة أخرى:

```python
translation_node = pipeline.translation(assetId=TRANSLATION_ASSET_ID)
output_node = pipeline.output(*args, **kwargs)
translation_node.link(output_node, 'data', 'output')
```

بالنسبة للعُقد التي تُنفّذ المخلوط `Outputable`، استخدم الصياغة المختصرة:

```python
output_node = translation_node.use_output('parameter_name_we_are_interested_in')
```

## عُقد الأصول والتعبئة التلقائية

تُستخدم عُقد الأصول لتشغيل النماذج ويجب أن تحتوي على معرّف أصل. بمجرد إنشائها، تحتوي عُقدة الأصل على جميع معلومات النموذج والمعاملات التي تُعبَّأ تلقائيًا من خلال التفاعل مع منصة Aixplain.

```python
translation_node = pipeline.translation(assetId=TRANSLATION_ASSET_ID)
print(translation_node.inputs)
print(translation_node.outputs)
```

## التعامل مع المعاملات

يتم الوصول إلى المعاملات عبر خاصيتَي `inputs` و`outputs` للعُقدة، حيث تعملان ككائنات وكيلة للمعاملات.

```python
print(translation_node.inputs.text)
print(translation_node.outputs.data)
```

أضف معاملات إلى عُقدة باستخدام `create_param` على خاصية `inputs` أو `outputs` المقابلة:

```python
translation_node.inputs.create_param('source_language', DataType.TEXT)
translation_node.outputs.create_param('source_audio', DataType.AUDIO)
```

بدلاً من ذلك، أنشئ المعاملات مباشرةً باستخدام فئتَي `InputParam` أو `OutputParam`:

```python
from aixplain.modules.pipeline.designer import InputParam, OutputParam

source_language = InputParam(
    code='source_language',
    dataType=DataType.TEXT,
    is_required=True,
    node=translation_node
)
```

أو أضف المعاملات بشكل صريح:

```python
source_audio = OutputParam(dataType=DataType.AUDIO, code='source_audio')
translation_node.outputs.add_param(source_audio)
```

عند الحاجة، يمكن تعيين قيمة أي معامل مباشرةً دون الحاجة إلى ربط العُقد:

```python
translation_node.inputs.text = 'This is example text to translate'
translation_node.inputs.source_language = 'en'
```

سيؤدي ذلك ضمنيًا إلى تعيين خاصية `value` لكائن المعامل.

## ربط العُقد

aربط العُقد لتمرير البيانات بينها باستخدام طريقة `link`. تربط هذه الطريقة مخرج عُقدة بمدخل عُقدة أخرى على المعاملات المحددة.

لنأخذ العُقد التالية بعين الاعتبار:

```python
input_node = pipeline.input()
translation_node = pipeline.translation(assetId=TRANSLATION_ASSET_ID)
```

اربط العُقد معًا:

```python
input_node.link(translation_node, 'input', 'text')
```

حدّد المعاملات بشكل صريح:

```python
input_node.link(translation_node, from_param='input', to_param='text')
```

أو استخدم نسخ المعاملات:

```python
input_node.link(translation_node, from_param=input_node.outputs.input, to_param=translation_node.inputs.text)
```

يمكنك أيضًا ربط المعاملات مباشرةً إذا وجدت ذلك أكثر ملاءمة:

```python
input_node.outputs.input.link(translation_node.inputs.text)
```

## التحقق من صحة خط المعالجة

استخدم طريقة `validate` للتأكد من أن خط المعالجة صالح وجاهز للتشغيل. تُطلق هذه الطريقة استثناءً إذا كان خط المعالجة يحتوي على مشكلات.

```python
pipeline.validate()
```

تتحقق هذه الطريقة مما يلي:
 * يحتوي على عُقدة مدخل واحدة على الأقل، وعُقدة أصل، وعُقدة مخرج
 * جميع عُقد المدخلات مرتبطة من الداخل، وعُقد المخرجات مرتبطة من الخارج، والبقية مرتبطة من الداخل والخارج
 * جميع الروابط تشير إلى العُقد الصحيحة والمعاملات المقابلة
 * جميع المعاملات المطلوبة إما مُعيَّنة أو مرتبطة
 * جميع المعاملات المرتبطة لها نفس نوع البيانات

وإلا تُطلق `ValueError` مع السبب إذا كان خط المعالجة غير صالح.

## حفظ وتشغيل خط المعالجة

احفظ خط المعالجة قبل تشغيله. تستدعي طريقة `save` ضمنيًا طريقة `validate`. استخدم طريقة `run` لتنفيذ خط المعالجة مع بيانات المدخل.

```python
pipeline.save() # Raises an exception if there are semantic issues
outputs = pipeline.run('This is example text to translate')
print(outputs)
```

يغطي هذا الدليل الاستخدام الأساسي للواجهة البرمجية (API) الخاصة بـ Aixplan SDK لإنشاء وتشغيل خطوط المعالجة. للحصول على ميزات أكثر تقدمًا، ارجع إلى الكود المصدري نفسه.

<!-- ملاحظات الترجمة: pipeline→خط معالجة | parameter→معامل | node→عُقدة (غير موجودة في المسرد، اختيرت كمصطلح تقني شائع) | asset→أصل (سياق المنصة) | mixin→مخلوط (مصطلح برمجي شائع) | kept EN: Aixplan, Aixplain, SDK, API, ValueError, Outputable — brand/code names -->