---
sidebar_label: process_media_files
title: aixplain.processes.data_onboarding.process_media_files
---

#### compress\_folder

```python
def compress_folder(folder_path: str) -> str
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/processes/data_onboarding/process_media_files.py#L25)

Compress a folder into a gzipped tar archive.

This function takes a folder and creates a compressed tar archive (.tgz)
containing all files in the folder. The archive is created in the same
directory as the input folder.

**Arguments**:

- `folder_path` _str_ - Path to the folder to be compressed.
  

**Returns**:

- `str` - Path to the created .tgz archive file.

#### run

```python
def run(metadata: MetaData,
        paths: List,
        folder: Path,
        batch_size: int = 100) -> Tuple[List[File], int, int, int, int]
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/processes/data_onboarding/process_media_files.py#L44)

Process media files and prepare them for upload to S3 with batch processing.

This function handles the processing and uploading of media files (audio, image, etc.)
to S3. It supports both local files and public URLs, processes them in batches,
and creates index files to track the media locations and any interval information.

The process works as follows:
1. For each media file in the input paths:
- If it&#x27;s a public URL: Add the URL to an index CSV file
- If it&#x27;s a local file: Copy to a temporary folder and add path to index
2. After every batch_size files:
- For local files: Compress the folder into .tgz and upload to S3
- Create and upload an index CSV file with paths and metadata
- Reset for the next batch

**Arguments**:

- `metadata` _MetaData_ - Metadata object containing information about the media type,
  storage type, and column mappings.
- `paths` _List_ - List of paths to CSV files containing media information.
- `folder` _Path_ - Local folder path where temporary files and compressed archives
  will be stored during processing.
- `batch_size` _int, optional_ - Number of media files to process in each batch.
  Defaults to 100.
  

**Returns**:

  Tuple[List[File], int, int, int, int]: A tuple containing:
  - List[File]: List of File objects pointing to uploaded index files in S3
  - int: Index of the data column in the index CSV
  - int: Index of the start column for intervals (-1 if not used)
  - int: Index of the end column for intervals (-1 if not used)
  - int: Total number of media files processed
  

**Raises**:

- `Exception` - If:
  - Input files are not found
  - Required columns are missing
  - File size limits are exceeded (50MB for audio, 25MB for others)
  - Invalid interval configurations are detected

