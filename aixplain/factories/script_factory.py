import os
import json
from typing import Tuple

import requests

from aixplain.utils import config


class ScriptFactory:
    @classmethod
    def upload_script(cls, script_path: str) -> Tuple[str, str]:
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
