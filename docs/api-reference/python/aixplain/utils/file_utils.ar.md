---
sidebar_label: file_utils
title: aixplain.utils.file_utils
---

حقوق النشر 2022 لمؤلفي aiXplain SDK

مرخّص بموجب رخصة Apache، الإصدار 2.0 ("الرخصة")؛
لا يجوز لك استخدام هذا الملف إلا وفقًا للرخصة.
يمكنك الحصول على نسخة من الرخصة على:

     http://www.apache.org/licenses/LICENSE-2.0

ما لم يكن مطلوبًا بموجب القانون المعمول به أو متفقًا عليه كتابيًا، يتم توزيع البرنامج
بموجب هذه الرخصة على أساس "كما هو" دون أي ضمانات أو شروط من أي نوع،
سواء كانت صريحة أو ضمنية.
راجع الرخصة للاطلاع على الأذونات والقيود المحددة بموجبها.

#### save\_file

```python
def save_file(
        download_url: Text,
        download_file_path: Optional[Union[str,
                                           Path]] = None) -> Union[str, Path]
```

<!-- ملاحظات الترجمة: أُبقيت أسماء الدوال والمعاملات بالإنجليزية لأنها شيفرة برمجية | kept EN: file_utils, save_file — function/module names | kept EN: aiXplain SDK — brand name | تُرجم نص رخصة Apache مع الحفاظ على بنية Markdown -->