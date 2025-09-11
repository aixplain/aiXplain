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

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/utils/validation_utils.py#L27)

Validate dataset parameters before onboarding.

This function performs comprehensive validation of dataset parameters to ensure
they meet the requirements for onboarding. It checks:
- Input/output data type compatibility with the specified function
- Presence of required input data
- Validity of dataset splitting configuration
- Presence of content data source

**Arguments**:

- `input_schema` _List[Union[Dict, MetaData]]_ - Metadata describing the input
  data structure and types.
- `output_schema` _List[Union[Dict, MetaData]]_ - Metadata describing the output
  data structure and types.
- `function` _Function_ - The function type that this dataset is designed for
  (e.g., translation, transcription).
- `input_ref_data` _Dict[Text, Any], optional_ - References to existing input
  data in the platform. Defaults to \{}.
- `metadata_schema` _List[Union[Dict, MetaData]], optional_ - Additional metadata
  describing the dataset. Defaults to [].
  content_path (Union[Union[Text, Path], List[Union[Text, Path]]], optional):
  Path(s) to local files containing the data. Defaults to [].
- `split_labels` _Optional[List[Text]], optional_ - Labels for dataset splits
  (e.g., [&quot;train&quot;, &quot;test&quot;]). Must be provided with split_rate.
  Defaults to None.
- `split_rate` _Optional[List[float]], optional_ - Proportions for dataset splits
  (e.g., [0.8, 0.2]). Must sum to 1.0 and match split_labels length.
  Defaults to None.
- `s3_link` _Optional[str], optional_ - S3 URL to data files or directories.
  Alternative to content_path. Defaults to None.
  

**Raises**:

- `AssertionError` - If any validation fails:
  - No input data specified
  - Incompatible input/output types for function
  - Invalid split configuration
  - No content source provided
  - Multiple split metadata entries
  - Invalid split metadata type
  - Mismatched split labels and rates
  

**Notes**:

  Either content_path or s3_link must be provided. If using splits,
  both split_labels and split_rate must be provided.

