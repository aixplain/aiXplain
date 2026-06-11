---
sidebar_label: validation_utils
title: aixplain.utils.validation_utils
---

#### dataset\_onboarding\_validation

```python
def dataset_onboarding_validation(input_schema: List[Union[Dict, MetaData]],
                                  output_schema: List[Union[Dict, MetaData]],
                                  function: Function,
                                  input_ref_data: Dict[Text, Any] = {},
                                  metadata_schema: List[Union[Dict,
                                                              MetaData]] = [],
                                  content_path: Union[Union[Text, Path],
                                                      List[Union[Text,
                                                                 Path]]] = [],
                                  split_labels: Optional[List[Text]] = None,
                                  split_rate: Optional[List[float]] = None,
                                  s3_link: Optional[str] = None) -> None
```

<!-- ملاحظات الترجمة: [لا يوجد نص نثري للترجمة — الملف يحتوي فقط على أسماء دوال وكتل شيفرة] | [kept EN: dataset_onboarding_validation — function name] | [kept EN: sidebar_label/title — code module paths] -->