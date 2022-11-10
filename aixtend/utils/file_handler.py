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


import tempfile
from pathlib import Path
from uuid import uuid4
import requests

def download_file(download_url: str, download_file_path=None) -> str:
    """Download and save file from given URL

    Args:
        download_url (str): URL of file to download
        download_file_path (str, optional): File path to save downloaded file. If None then generates random path is tempdirectory. Defaults to None.

    Returns:
        str: Path where file was downloaded
    """
    if download_file_path is None:
        sys_temp_dir = tempfile.gettempdir()
        save_dir = Path(sys_temp_dir) / "aiXtend"
        save_dir.mkdir(parents=True, exist_ok=True)
        file_ext = Path(download_url).suffix.split('?')[0]
        download_file_path = save_dir / (str(uuid4()) + file_ext)
    r = requests.get(download_url)
    with open(download_file_path, 'wb') as f:
        f.write(r.content)
    return download_file_path

