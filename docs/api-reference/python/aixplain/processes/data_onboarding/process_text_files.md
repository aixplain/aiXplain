---
sidebar_label: process_text_files
title: aixplain.processes.data_onboarding.process_text_files
---

#### process\_text

```python
def process_text(content: str, storage_type: StorageType) -> Text
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/processes/data_onboarding/process_text_files.py#L18)

Process text content based on its storage type and location.

This function handles different types of text content:
- Local files: Reads the file content (with size validation)
- URLs: Marks them for non-download if they&#x27;re public links
- Direct text: Uses the content as-is

**Arguments**:

- `content` _str_ - The text content to process. Can be:
  - A path to a local file
  - A URL pointing to text content
  - The actual text content
- `storage_type` _StorageType_ - The type of storage for the content:
  - StorageType.FILE for local files
  - StorageType.TEXT for direct text content
  - Other storage types for different handling
  

**Returns**:

- `Text` - The processed text content. URLs may be prefixed with
  &quot;DONOTDOWNLOAD&quot; if they should not be downloaded.
  

**Raises**:

- `AssertionError` - If a local text file exceeds 25MB in size.
- `IOError` - If there are issues reading a local file.

#### run

```python
def run(metadata: MetaData,
        paths: List,
        folder: Path,
        batch_size: int = 1000) -> Tuple[List[File], int, int]
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/processes/data_onboarding/process_text_files.py#L65)

Process text files in batches and upload them to S3 with index tracking.

This function processes text files (either local or from URLs) in batches,
creating compressed CSV index files that track the text content and their
positions. The index files are then uploaded to S3.

The process works as follows:
1. For each input CSV file:
- Read the specified column containing text content/paths
- Process each text entry (read files, handle URLs)
- Add processed text to the current batch
2. After every batch_size entries:
- Create a new index CSV with the processed texts
- Add row indices for tracking
- Compress and upload the index to S3
- Start a new batch

**Arguments**:

- `metadata` _MetaData_ - Metadata object containing information about the text data,
  including column names and storage type configuration.
- `paths` _List_ - List of paths to CSV files containing the text data or
  references to text content.
- `folder` _Path_ - Local folder path where the generated index files will be
  temporarily stored before upload.
- `batch_size` _int, optional_ - Number of text entries to process in each batch.
  Defaults to 1000.
  

**Returns**:

  Tuple[List[File], int, int]: A tuple containing:
  - List[File]: List of File objects pointing to uploaded index files in S3
  - int: Index of the data column in the index CSV files
  - int: Total number of text entries processed
  

**Raises**:

- `Exception` - If:
  - Input CSV files are not found
  - Required columns are missing in input files
  - Text processing fails (e.g., file size limit exceeded)

