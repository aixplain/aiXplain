"""
Copyright 2022 The aiXplain SDK authors

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

     http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

import os
import re
import requests

import aixplain.utils.config as config
from aixplain.enums.license import License
from aixplain.utils.request_utils import _request_with_retry
from collections import defaultdict
from pathlib import Path
from typing import Any, Optional, Text, Union, Dict, List
from uuid import uuid4
from urllib.parse import urljoin, urlparse
from pandas import DataFrame


def save_file(download_url: Text, download_file_path: Optional[Union[str, Path]] = None) -> Union[str, Path]:
    """Download and save a file from a given URL.

    This function downloads a file from the specified URL and saves it either
    to a specified path or to a generated path in the 'aiXplain' directory.

    Args:
        download_url (Text): URL of the file to download.
        download_file_path (Optional[Union[str, Path]], optional): Path where the
            downloaded file should be saved. If None, generates a folder 'aiXplain'
            in the current working directory and saves the file there with a UUID
            name. Defaults to None.

    Returns:
        Union[str, Path]: Path where the file was downloaded.

    Note:
        If download_file_path is None, the file will be saved with a UUID name
        and the original file extension in the 'aiXplain' directory.
    """
    if download_file_path is None:
        save_dir = os.getcwd()
        save_dir = Path(save_dir) / "aiXplain"
        save_dir.mkdir(parents=True, exist_ok=True)
        file_ext = Path(download_url).suffix.split("?")[0]
        download_file_path = save_dir / (str(uuid4()) + file_ext)
    r = _request_with_retry("get", download_url)
    with open(download_file_path, "wb") as f:
        f.write(r.content)
    return download_file_path


def download_data(url_link: str, local_filename: Optional[str] = None) -> str:
    """Download a file from a URL with streaming support.

    This function downloads a file from the specified URL using streaming to
    handle large files efficiently. The file is downloaded in chunks to
    minimize memory usage.

    Args:
        url_link (str): URL of the file to download.
        local_filename (Optional[str], optional): Local path where the file
            should be saved. If None, uses the last part of the URL as the
            filename. Defaults to None.

    Returns:
        str: Path to the downloaded file.

    Raises:
        requests.exceptions.RequestException: If the download fails or the
            server returns an error status.
    """
    if local_filename is None:
        local_filename = url_link.split("/")[-1]
    with requests.get(url_link, stream=True) as r:
        r.raise_for_status()
        with open(local_filename, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                # If you have chunk encoded response uncomment if
                # and set chunk_size parameter to None.
                # if chunk:
                f.write(chunk)
    return local_filename


def upload_data(
    file_name: Union[Text, Path],
    tags: Optional[List[Text]] = None,
    license: Optional[License] = None,
    is_temp: bool = True,
    content_type: Text = "text/csv",
    content_encoding: Optional[Text] = None,
    nattempts: int = 2,
    return_download_link: bool = False,
    api_key: Optional[Text] = None,
):
    """Upload a file to S3 using pre-signed URLs with retry support.

    This function handles file uploads to S3 by first obtaining a pre-signed URL
    from the aiXplain backend and then using it to upload the file. It supports
    both temporary and permanent storage with optional metadata like tags and
    license information.

    Args:
        file_name (Union[Text, Path]): Local path of the file to upload.
        tags (Optional[List[Text]], optional): List of tags to associate with
            the file. Only used when is_temp is False. Defaults to None.
        license (Optional[License], optional): License to associate with the file.
            Only used when is_temp is False. Defaults to None.
        is_temp (bool, optional): Whether to upload as a temporary file.
            Temporary files have different handling and URL generation.
            Defaults to True.
        content_type (Text, optional): MIME type of the content being uploaded.
            Defaults to "text/csv".
        content_encoding (Optional[Text], optional): Content encoding of the file
            (e.g., 'gzip'). Defaults to None.
        nattempts (int, optional): Number of retry attempts for upload failures.
            Defaults to 2.
        return_download_link (bool, optional): If True, returns a direct download
            URL instead of the S3 path. Defaults to False.
        api_key (Optional[Text], optional): API key for authentication.
            Defaults to None, using the configured TEAM_API_KEY.

    Returns:
        str: Either an S3 path (s3://bucket/key) or a download URL, depending
            on return_download_link parameter.

    Raises:
        Exception: If the upload fails after all retry attempts.

    Note:
        The function will automatically retry failed uploads up to nattempts
        times before raising an exception.
    """
    try:
        # Get pre-signed URL
        # URL of aiXplain service which returns a pre-signed URL to onboard the file
        if is_temp is True:
            url = urljoin(config.BACKEND_URL, "sdk/file/upload/temp-url")
            payload = {"contentType": content_type, "originalName": os.path.basename(file_name)}
        else:
            url = urljoin(config.BACKEND_URL, "sdk/file/upload-url")
            if tags is None:
                tags = []
            payload = {"contentType": content_type, "originalName": file_name, "tags": ",".join(tags), "license": license.value}

        team_key = api_key or config.TEAM_API_KEY
        headers = {"Authorization": "token " + team_key}

        r = _request_with_retry("post", url, headers=headers, data=payload)
        response = r.json()
        path = response["key"]
        # Upload data
        presigned_url = response["uploadUrl"]  # pre-signed URL
        download_link = response.get("downloadUrl", "")
        headers = {"Content-Type": content_type}
        if content_encoding is not None:
            headers["Content-Encoding"] = content_encoding
        payload = open(file_name, "rb").read()
        # saving the file into the pre-signed URL
        r = _request_with_retry("put", presigned_url, headers=headers, data=payload)

        # if the process fail, try one more
        if r.status_code != 200:
            if nattempts > 0:
                return upload_data(
                    file_name=file_name,
                    content_type=content_type,
                    tags=tags,
                    license=license,
                    is_temp=is_temp,
                    content_encoding=content_encoding,
                    nattempts=nattempts - 1,
                    return_download_link=return_download_link,
                )
            else:
                raise Exception("File Uploading Error: Failure on Uploading to S3.")
        if return_download_link is False:
            bucket_name = re.findall(r"https://(.*?).s3.amazonaws.com", presigned_url)[0]
            s3_link = f"s3://{bucket_name}/{path}"
            return s3_link
        return download_link
    except Exception:
        if nattempts > 0:
            return upload_data(
                file_name=file_name,
                content_type=content_type,
                tags=tags,
                license=license,
                is_temp=is_temp,
                content_encoding=content_encoding,
                nattempts=nattempts - 1,
                return_download_link=return_download_link,
            )
        else:
            raise Exception("File Uploading Error: Failure on Uploading to S3.")


def s3_to_csv(
    s3_url: Text,
    aws_credentials: Optional[Dict[Text, Text]] = {"AWS_ACCESS_KEY_ID": None, "AWS_SECRET_ACCESS_KEY": None}
) -> str:
    """Convert S3 directory contents to a CSV file with file listings.

    This function takes an S3 URL and creates a CSV file containing listings
    of all files in that location. It handles both single files and directories,
    with special handling for directory structures.

    Args:
        s3_url (Text): S3 URL in the format 's3://bucket-name/path'.
        aws_credentials (Optional[Dict[Text, Text]], optional): AWS credentials
            dictionary with 'AWS_ACCESS_KEY_ID' and 'AWS_SECRET_ACCESS_KEY'.
            If not provided or values are None, uses environment variables.
            Defaults to {"AWS_ACCESS_KEY_ID": None, "AWS_SECRET_ACCESS_KEY": None}.

    Returns:
        str: Path to the generated CSV file. The file contains listings of
            all files found in the S3 location.

    Raises:
        Exception: If:
            - boto3 is not installed
            - Invalid S3 URL format
            - AWS credentials are missing
            - Bucket doesn't exist
            - No files found
            - Files are at bucket root
            - Directory structure is invalid (unequal file counts or mismatched names)

    Note:
        - The function requires the boto3 package to be installed
        - The generated CSV will have a UUID as filename
        - For directory structures, all subdirectories must have the same
          number of files with matching prefixes
    """
    try:
        import boto3
        from botocore.exceptions import NoCredentialsError
    except ModuleNotFoundError:
        raise Exception(
            "boto3 is not currently installed in your project environment. Please try installing it using pip:\n\npip install boto3"
        )
    url = urlparse(s3_url)
    if url.scheme != "s3":
        raise Exception("the url is not an s3 url")
    bucket_name = url.netloc
    prefix = url.path[1:]
    try:
        aws_access_key_id = aws_credentials.get("AWS_ACCESS_KEY_ID") or os.getenv("AWS_ACCESS_KEY_ID")
        aws_secret_access_key = aws_credentials.get("AWS_SECRET_ACCESS_KEY") or os.getenv("AWS_SECRET_ACCESS_KEY")
        s3 = boto3.client("s3", aws_access_key_id=aws_access_key_id, aws_secret_access_key=aws_secret_access_key)
        response = s3.list_objects_v2(Bucket=bucket_name, Prefix=prefix)
    except NoCredentialsError:
        raise Exception(
            "to use the s3 bucket option you need to set the right AWS credentials [AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY]"
        )
    except Exception:
        raise Exception("the bucket you are trying to use does not exist")

    try:
        files = []

        if "Contents" in response:
            for obj in response["Contents"]:
                files.append(obj["Key"])

        # check if no files where found
        if not files:
            raise Exception(f"ERROR No files were found => bucket name: {bucket_name}, prefix: {prefix}")

        response2 = s3.list_objects_v2(Bucket=bucket_name, Prefix=prefix, Delimiter="/")
        if "CommonPrefixes" in response2:
            there_are_folders = bool(response2["CommonPrefixes"])
        else:
            there_are_folders = False

        # check if there are folder or if the files in the root of the url, and reformart the paths
        if there_are_folders:
            data = defaultdict(list)
            for path in files:
                directory = path.rsplit("/", 2)[-2]
                data[directory].append(f"s3://{bucket_name}/{path}")

            # validate all the folders have the same length
            first_key = list(data.keys())[0]
            main_len = len(data[first_key])
            if any(main_len != len(val) for val in data.values()):
                raise Exception("all the directories should have the same number of files")

            # validate that the names of the files are the same in all the list
            if len(data.keys()) > 1:
                for i in range(main_len):
                    main_file_name = Path(data[first_key][i]).stem
                    for val in data.values():
                        if Path(val[i]).stem != main_file_name:
                            raise Exception("all the files in different directories should have the same prefix")

        elif prefix == "":
            raise Exception("ERROR the files can't be at the root of the bucket ")
        else:
            data = {prefix: [f"s3://{bucket_name}/{file}" for file in files]}

        # create DataFrame and convert it to csv
        df = DataFrame(data)
        output_path = f"{uuid4()}.csv"
        df.to_csv(output_path, index=False)

        return output_path
    except (Exception, ValueError) as e:
        raise Exception(e)
