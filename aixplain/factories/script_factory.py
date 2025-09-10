import os
import json
from typing import Tuple

import requests

from aixplain.utils import config


class ScriptFactory:
    """A factory class for handling script file operations.

    This class provides functionality for uploading script files to the backend
    and managing their metadata.
    """
    @classmethod
    def upload_script(cls, script_path: str) -> Tuple[str, str]:
        """Uploads a script file to the backend and returns its ID and metadata.

        Args:
            script_path (str): The file system path to the script file to be uploaded.

        Returns:
            Tuple[str, str]: A tuple containing:
                - file_id (str): The unique identifier assigned to the uploaded file.
                - metadata (str): JSON string containing file metadata (name and size).

        Raises:
            Exception: If the upload fails or the file cannot be accessed.
        """
        try:
            url = f"{config.BACKEND_URL}/sdk/pipelines/script"
            headers = {"Authorization": f"Token {config.TEAM_API_KEY}"}
            r = requests.post(url, headers=headers, files={"file": open(script_path, "rb")})
            if 200 <= r.status_code < 300:
                response = r.json()
            else:
                raise Exception()
        except Exception:
            response = {"fileId": ""}

        # get metadata info
        fname = os.path.splitext(os.path.basename(script_path))[0]
        file_size = int(os.path.getsize(script_path))
        metadata = json.dumps({"name": fname, "size": file_size})
        return response["fileId"], metadata
