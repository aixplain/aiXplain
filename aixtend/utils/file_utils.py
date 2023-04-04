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

import aixtend.utils.config as config
import os
import re
import requests
import validators

from aixtend.enums.storage_type import StorageType
from pathlib import Path
from uuid import uuid4
from requests.adapters import HTTPAdapter, Retry
from typing import Any, Dict, Optional, Text, Union


def check_storage_type(input_link: Any) -> StorageType:
    """Check whether a path is a URL (s3 link or HTTP link), a file or a textual content

    Args:
        input_link (Any): path to be checked

    Returns:
        StorageType: URL, TEXT or FILE
    """
    if os.path.exists(input_link) is True:
        return StorageType.FILE
    elif (
        input_link.startswith("s3://")
        or input_link.startswith("http://")
        or input_link.startswith("https://")
        or validators.url(input_link)
    ):
        return StorageType.URL
    else:
        return StorageType.TEXT


def save_file(download_url: Text, download_file_path: Optional[Any] = None) -> Any:
    """Download and save file from given URL

    Args:
        download_url (Text): URL of file to download
        download_file_path (Any, optional): File path to save downloaded file. If None then generates a folder 'aiXtend' in current working directory. Defaults to None.

    Returns:
        Text: Path where file was downloaded
    """
    if download_file_path is None:
        save_dir = os.getcwd()
        save_dir = Path(save_dir) / "aiXtend"
        save_dir.mkdir(parents=True, exist_ok=True)
        file_ext = Path(download_url).suffix.split("?")[0]
        download_file_path = save_dir / (str(uuid4()) + file_ext)
    r = _request_with_retry("get", download_url)
    with open(download_file_path, "wb") as f:
        f.write(r.content)
    return download_file_path


def _request_with_retry(method: Text, url: Text, **params) -> requests.Response:
    """Wrapper around requests with Session to retry in case it fails

    Args:
        method (Text): HTTP method, such as 'GET' or 'HEAD'.
        url (Text): The URL of the resource to fetch.
        **params: Params to pass to request function

    Returns:
        requests.Response: Response object of the request
    """
    session = requests.Session()
    retries = Retry(total=5, backoff_factor=0.1, status_forcelist=[500, 502, 503, 504])
    session.mount("https://", HTTPAdapter(max_retries=retries))
    response = session.request(method=method.upper(), url=url, **params)
    return response


def download_data(url_link, local_filename=None):
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
    file_name: Union[Text, Path], content_type: Text = "text/csv", content_encoding: Optional[Text] = None, nattempts: int = 0
):
    """Upload files to S3 with pre-signed URLs

    Args:
        file_name (Union[Text, Path]): local path of file to be uploaded
        content_type (Text, optional): Type of content. Defaults to "text/csv".
        content_encoding (Text, optional): Content encoding. Defaults to None.
        nattempts (int, optional): Number of attempts for diminish the risk of exceptions. Defaults to 0.

    Returns:
        URL: s3 path
    """
    try:
        # Get pre-signed URL
        team_key = config.TEAM_API_KEY
        url = config.TEMPFILE_UPLOAD_URL

        headers = {"Authorization": "token " + team_key}

        payload = {"contentType": content_type, "originalName": file_name}
        r = _request_with_retry("post", url, headers=headers, data=payload)
        response = r.json()
        path = response["key"]
        # Upload data
        presigned_url = response["uploadUrl"]
        headers = {"Content-Type": content_type}
        if content_encoding is not None:
            headers["Content-Encoding"] = content_encoding
        payload = open(file_name, "rb").read()
        r = _request_with_retry("put", presigned_url, headers=headers, data=payload)

        if r.status_code != 200:
            if nattempts == 0:
                return upload_data(file_name, content_type, content_encoding, nattempts + 1)
            else:
                raise Exception("File Uploading Error: Failure on Uploading to S3.")
        bucket_name = re.findall(r"https://(.*?).s3.amazonaws.com", presigned_url)[0]
        s3_link = f"s3://{bucket_name}/{path}"
        return s3_link
    except Exception as e:
        if nattempts == 0:
            return upload_data(file_name, content_type, content_encoding, nattempts + 1)
        else:
            raise Exception("File Uploading Error: Failure on Uploading to S3.")


def path2link(data: Union[Text, Dict]) -> Union[Text, Dict]:
    """If user input data is a local file, upload to aiXplain platform

    Args:
        data (Union[Text, Dict]): input data

    Returns:
        Union[Text, Dict]: input links/texts
    """

    def check_file(local_path):
        if os.path.exists(local_path) is False:
            raise Exception(f'File Upload Error: local file "{local_path}" not found.')
        if os.path.getsize(local_path) > 10485760:
            raise Exception(f'File Upload Error: local file "{local_path}" exceeds 10 MB.')

    if isinstance(data, str):
        if check_storage_type(data) == StorageType.FILE:
            check_file(data)
            data = upload_data(file_name=data)
    else:
        for key in data:
            if isinstance(data[key], str):
                if check_storage_type(data[key]) == StorageType.FILE:
                    check_file(data[key])
                    data[key] = upload_data(file_name=data[key])
    return data
