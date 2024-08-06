from typing import List, Text, Optional
import logging
import json
from urllib.parse import urljoin
from aixplain.modules.e2e_search.cost import E2eSearchCost
from aixplain.factories.model_factory import ModelFactory
from aixplain.modules.asset import Asset
from aixplain.modules.dataset import Dataset
from aixplain.modules.model import Model

from aixplain.utils import config
from aixplain.utils.file_utils import _request_with_retry


class E2eSearch(Asset):
    """E2eSearch is a powerful tool for searching for the bootstrapped e2e model that can replace a given pipeline.

    Attributes:
        name (Text): Name of the E2eSearch.
        dataset (Dataset): Dataset to train and evaluate the bootstrapped models.
        cost (Cost): Cost of the E2eSearch.
        id (Text): ID of the E2eSearch.
        in_language (Text): language of the input
        in_modality (Text): modality of the input
        in_ids (List[Text]): list of input columns Ids
        out_language (Text): language of the output
        out_modality (Text): modality of the output
        out_ids (List[Text]): list of output columns Ids
        eval_size (float): percentage of evalset.
        description (Text): Description of the E2eSearch.
        supplier (Text): Supplier of the E2eSearch.
        version (Text): Version of the E2eSearch.
        additional_info (dict): Additional information to be saved with the E2eSearch.
        backend_url (str): URL of the backend.
        api_key (str): The TEAM API key used for authentication.
    """

    def __init__(
        self,
        name: Text,
        dataset: Dataset,
        cost: E2eSearchCost,
        id: Optional[Text],
        in_language: Text,
        in_modality: Text,
        in_ids: List[Text],
        out_language: Optional[Text],
        out_modality: Text,
        out_ids: List[Text],
        eval_size: float,
        description: Optional[Text] = "",
        supplier: Optional[Text] = "aiXplain",
        version: Optional[Text] = "1.0",
        **additional_info,
    ) -> None:
        super().__init__(id, name, description, supplier, version)
        self.dataset = dataset
        self.cost = cost
        self.in_language = in_language,
        self.in_modality = in_modality,
        self.in_ids = in_ids,
        self.out_language = out_language,
        self.out_modality = out_modality,
        self.out_ids = out_ids,
        self.eval_size = eval_size,
        self.additional_info = additional_info
        self.backend_url = config.BACKEND_URL
        self.api_key = config.TEAM_API_KEY
        self.aixplain_key = config.AIXPLAIN_API_KEY

    def start(self) -> Model:
        """Start the E2eSearch job.

        Returns:
            Model: The model object representing the E2eSearch job.
        """
        payload = {}
        try:
            url = urljoin(self.backend_url, f"sdk/e2eSearch")
            headers = {"Authorization": f"Token {self.api_key}", "Content-Type": "application/json"}
            payload = {
                "name": self.name,
                "dataset": {
                        "dataset_id": self.dataset.id,
                        "in_ids": self.in_ids,
                        "out_ids": self.out_ids,
                        "eval_size": self.eval_size
                    },
                "modality": {
                    "in_modality": self.in_modality,
                    "out_modality": self.out_modality,
                }
            }
            language = {}
            if self.in_language is not None:
                language["in_language"] = self.in_language
            if self.out_language is not None:
                language["out_language"] = self.out_language
            payload["language"] = language
            logging.info(f"Start service for POST Start E2eSearch - {url} - {headers} - {json.dumps(payload)}")
            r = _request_with_retry("post", url, headers=headers, json=payload)
            resp = r.json()
            logging.info(f"Response for POST Start E2eSearch - Name: {self.name} / Status {resp}")
            return ModelFactory().get(resp["id"])
        except Exception:
            message = ""
            if resp is not None and "statusCode" in resp:
                status_code = resp["statusCode"]
                message = resp["message"]
                message = f"Status {status_code} - {message}"
            error_message = f"Start E2eSearch: Error with payload {json.dumps(payload)}: {message}"
            logging.exception(error_message)
            return None
