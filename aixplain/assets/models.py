from typing import Dict, Union, Text

import logging
import json
import requests

from urllib.parse import urljoin
from aixplain.assets.base import BaseAsset, GetAssetMixin, ListAssetMixin
from aixplain.assets.files import File
from aixplain import config

logger = logging.getLogger(__name__)


class Model(BaseAsset, GetAssetMixin, ListAssetMixin):
    """
    Model class that extends BaseAsset, GetAssetMixin, and ListAssetMixin.
    This class is responsible for handling model-related operations and assets,
    including running models synchronously and asynchronously.
    """

    asset_path = 'models'

    def run(self, data: Union[Text, Dict], name: Text = "model_process",
            timeout: float = 300, parameters: Dict = {}, models_run_url: Text = None,
            wait_time: float = 0.5) -> Dict:
        """
        Runs the model synchronously.

        :param data: Input data for the model in Text or Dict format.
        :param name: Name of the model process (default is "model_process").
        :param timeout: Timeout for the model execution in seconds
                        (default is 300).
        :param parameters: Additional parameters for the model execution.
        :param wait_time: Time to wait between status checks in seconds
                          (default is 0.5).
        :return: Dictionary containing the result of the model execution.
        :raises NotImplementedError: This method must be implemented in a
                                     subclass.
        """
        raise NotImplementedError()

    def run_async(self, input: Union[Text, Dict], name: Text = 'model_process',
                  parameters: Dict = {}, models_run_url: Text = None) -> Dict:
        """
        Runs the model asynchronously.

        :param input: Input data for the model in Text or Dict format.
        :param name: Name of the model process (default is "model_process").
        :param models_run_url: Model run url
                               (fallbacks to config.MODELS_RUN_URL)
        :param parameters: Additional parameters for the model execution.
        :return: Dictionary containing the status of the asynchronous execution
                 and the result URL or an error.
        """

        models_run_url = models_run_url or config.MODELS_RUN_URL
        data = File.batch_upload_to_s3(input)

        try:
            data = json.loads(data)
            if not isinstance(data, dict):
                data = str(data)  # Assumes int, float or str
        except ValueError:
            pass

        payload = {'data': data}
        payload.update(parameters or {})

        url = urljoin(models_run_url, self.id)

        try:
            result = self.client.request('POST', url, json=payload)
            result_json = result.json()
            return {'status': 'IN_PROGRESS', 'url': result_json['data']}
        except Exception as e:
            error = None
            if isinstance(e, requests.RequestException):
                if e.response is not None:
                    try:
                        error = e.response.json().get('error')
                    except Exception:
                        error = e.response.content
            logger.exception(e)
            logger.error(f'Failed to run: {name}, see above the reason')
            return {
                'status': 'FAILED',
                'error': error
            }
