---
sidebar_label: onboard_functions
title: aixplain.processes.data_onboarding.onboard_functions
---

#### get\_paths

```python
def get_paths(input_paths: List[Union[str, Path]]) -> List[Path]
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/processes/data_onboarding/onboard_functions.py#L40)

Recursively collect all supported local file paths from the given input paths.

This function traverses through the provided paths, which can be files or directories,
and collects paths to all supported files (currently only CSV files). It also performs
size validation to ensure files don&#x27;t exceed 1GB.

**Arguments**:

- `input_paths` _List[Union[str, Path]]_ - List of input paths. Can include both
  individual file paths and directory paths.
  

**Returns**:

- `List[Path]` - List of validated local file paths that are supported.
  

**Raises**:

- `AssertionError` - If any CSV file exceeds 1GB in size.
- `Warning` - If a file has an unsupported extension.

#### process\_data\_files

```python
def process_data_files(
    data_asset_name: str,
    metadata: MetaData,
    paths: List,
    folder: Optional[Union[str, Path]] = None
) -> Tuple[List[File], int, int, int, int]
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/processes/data_onboarding/onboard_functions.py#L83)

Process data files based on their type and prepare them for upload to S3.

This function handles different types of data files (audio, image, text, etc.)
by delegating to appropriate processing modules. It compresses the files if needed
and prepares them for upload to S3.

**Arguments**:

- `data_asset_name` _str_ - Name of the data asset being processed.
- `metadata` _MetaData_ - Metadata object containing type and subtype information
  for the data being processed.
- `paths` _List_ - List of paths to local files that need processing.
- `folder` _Optional[Union[str, Path]], optional_ - Local folder to save processed
  files before uploading to S3. If None, uses data_asset_name. Defaults to None.
  

**Returns**:

  Tuple[List[File], int, int, int, int]: A tuple containing:
  - List[File]: List of processed file objects ready for S3 upload
  - int: Index of the data column
  - int: Index of the start column (for intervals)
  - int: Index of the end column (for intervals)
  - int: Total number of rows processed

#### build\_payload\_data

```python
def build_payload_data(data: Data) -> Dict
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/processes/data_onboarding/onboard_functions.py#L129)

Build a payload dictionary for data onboarding to the core engine.

This function creates a standardized payload structure for onboarding data
to the core engine. It includes data properties, file information, and metadata
such as languages and column mappings.

**Arguments**:

- `data` _Data_ - Data object containing information about the data to be onboarded,
  including name, type, files, and language information.
  

**Returns**:

- `Dict` - A dictionary containing the formatted payload with the following key fields:
  - name: Name of the data
  - dataColumn: Column identifier for the data
  - dataType: Type of the data
  - dataSubtype: Subtype of the data
  - batches: List of file information with paths and order
  - tags: List of descriptive tags
  - metaData: Additional metadata including languages
  Additional fields may be added for interval data (start/end columns).

#### build\_payload\_corpus

```python
def build_payload_corpus(corpus: Corpus, ref_data: List[Text],
                         error_handler: ErrorHandler) -> Dict
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/processes/data_onboarding/onboard_functions.py#L174)

Build a payload dictionary for corpus onboarding to the core engine.

This function creates a standardized payload structure for onboarding a corpus,
including all its associated data, metadata, and configuration settings.

**Arguments**:

- `corpus` _Corpus_ - Corpus object containing the data collection to be onboarded,
  including name, description, functions, and associated data.
- `ref_data` _List[Text]_ - List of referenced data IDs that this corpus depends on
  or is related to.
- `error_handler` _ErrorHandler_ - Configuration for how to handle rows that fail
  during the onboarding process.
  

**Returns**:

- `Dict` - A dictionary containing the formatted payload with the following key fields:
  - name: Name of the corpus
  - description: Description of the corpus
  - suggestedFunctions: List of suggested AI functions
  - onboardingErrorsPolicy: Error handling policy
  - tags: List of descriptive tags
  - pricing: Pricing configuration
  - privacy: Privacy settings
  - license: License information
  - refData: Referenced data IDs
  - data: List of data payloads for each data component

#### build\_payload\_dataset

```python
def build_payload_dataset(dataset: Dataset, input_ref_data: Dict[Text, Any],
                          output_ref_data: Dict[Text, List[Any]],
                          hypotheses_ref_data: Dict[Text, Any],
                          meta_ref_data: Dict[Text, Any], tags: List[Text],
                          error_handler: ErrorHandler) -> Dict
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/processes/data_onboarding/onboard_functions.py#L220)

Build a payload dictionary for dataset onboarding to the core engine.

This function creates a comprehensive payload structure for onboarding a dataset,
including all its components: input data, output data, hypotheses, and metadata.
It handles both new data and references to existing data.

**Arguments**:

- `dataset` _Dataset_ - Dataset object to be onboarded, containing all the data
  components and configuration.
- `input_ref_data` _Dict[Text, Any]_ - Dictionary mapping input names to existing
  data IDs in the system.
- `output_ref_data` _Dict[Text, List[Any]]_ - Dictionary mapping output names to
  lists of existing data IDs for multi-reference outputs.
- `hypotheses_ref_data` _Dict[Text, Any]_ - Dictionary mapping hypothesis names to
  existing data IDs for model outputs or predictions.
- `meta_ref_data` _Dict[Text, Any]_ - Dictionary mapping metadata names to existing
  metadata IDs in the system.
- `tags` _List[Text]_ - List of descriptive tags for the dataset.
- `error_handler` _ErrorHandler_ - Configuration for how to handle rows that fail
  during the onboarding process.
  

**Returns**:

- `Dict` - A dictionary containing the formatted payload with the following sections:
  - Basic information (name, description, function, etc.)
  - Configuration (error handling, privacy, license)
  - Input data section with both new and referenced inputs
  - Output data section with both new and referenced outputs
  - Hypotheses section with both new and referenced hypotheses
  - Metadata section with both new and referenced metadata

#### create\_data\_asset

```python
def create_data_asset(payload: Dict,
                      data_asset_type: Text = "corpus",
                      api_key: Optional[Text] = None) -> Dict
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/processes/data_onboarding/onboard_functions.py#L355)

Create a new data asset (corpus or dataset) in the core engine.

This function sends the onboarding request to the core engine and handles the response.
It supports both corpus and dataset creation with proper authentication.

**Arguments**:

- `payload` _Dict_ - The complete payload for the data asset, containing all necessary
  information for onboarding (structure depends on data_asset_type).
- `data_asset_type` _Text, optional_ - Type of data asset to create. Must be either
  &quot;corpus&quot; or &quot;dataset&quot;. Defaults to &quot;corpus&quot;.
- `api_key` _Optional[Text], optional_ - Team API key for authentication. If None,
  uses the default key from config. Defaults to None.
  

**Returns**:

- `Dict` - A dictionary containing the onboarding status with the following fields:
  - success (bool): Whether the operation was successful
  - asset_id (str): ID of the created asset (if successful)
  - status (str): Current status of the asset (if successful)
  - error (str): Error message (if not successful)
  

**Notes**:

  The function handles both successful and failed responses, providing appropriate
  error messages in case of failure.

#### is\_data

```python
def is_data(data_id: Text) -> bool
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/processes/data_onboarding/onboard_functions.py#L413)

Check if a data object exists in the system by its ID.

This function makes an API call to verify the existence of a data object
in the system. It&#x27;s typically used to validate references before creating
new assets that depend on existing data.

**Arguments**:

- `data_id` _Text_ - The ID of the data object to check.
  

**Returns**:

- `bool` - True if the data exists and is accessible, False otherwise.
  Returns False in case of API errors or if the data is not found.
  

**Notes**:

  The function handles API errors gracefully, returning False instead
  of raising exceptions.

#### split\_data

```python
def split_data(paths: List, split_rate: List[float],
               split_labels: List[Text]) -> MetaData
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/processes/data_onboarding/onboard_functions.py#L446)

Split data files into partitions based on specified rates and labels.

This function adds a new column to CSV files to indicate the split assignment
for each row. It randomly assigns rows to splits based on the provided rates.
The function tries to find an unused column name for the split information.

**Arguments**:

- `paths` _List_ - List of paths to CSV files that need to be split.
- `split_rate` _List[float]_ - List of proportions for each split. Should sum to 1.0.
  For example, [0.8, 0.1, 0.1] for train/dev/test split.
- `split_labels` _List[Text]_ - List of labels corresponding to each split rate.
  For example, [&quot;train&quot;, &quot;dev&quot;, &quot;test&quot;].
  

**Returns**:

- `MetaData` - A metadata object for the new split column with:
  - name: The generated column name for the split
  - dtype: Set to DataType.LABEL
  - dsubtype: Set to DataSubtype.SPLIT
  - storage_type: Set to StorageType.TEXT
  

**Raises**:

- `Exception` - If no available column name is found or if file operations fail.
  

**Notes**:

  The function modifies the input CSV files in place, adding the new split column.

