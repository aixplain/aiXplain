import logging
from typing import Dict, List, Optional, Text, Union
import json
from aixplain.factories.dataset_factory import DatasetFactory
from aixplain.factories.model_factory import ModelFactory
from aixplain.modules.e2e_search import E2eSearch
from aixplain.modules.e2e_search.cost import E2eSearchCost
from aixplain.modules.dataset import Dataset
from aixplain.modules.model import Model
from aixplain.utils import config
from aixplain.utils.file_utils import _request_with_retry
from urllib.parse import urljoin 


class E2eSearchFactory:
    """A static class for creating and managing the E2eSearch experience.

    Attributes:
        backend_url (str): The URL for the backend.
    """

    aixplain_key = config.AIXPLAIN_API_KEY
    backend_url = config.BACKEND_URL

    @classmethod
    def _create_cost_from_response(cls, response: Dict) -> E2eSearchCost:
        """Create a Cost object from the response dictionary.

        Args:
            response (Dict): The response dictionary containing cost information.

        Returns:
            Cost: The Cost object created from the response.
        """
        return E2eSearchCost(response["trainingCost"], response["inferenceCost"], response["hostingCost"])

    @classmethod
    def create(
        cls,
        name: Text,
        dataset: Dataset,
        in_language: Text,
        in_modality: Text,
        in_ids: List[Text],
        out_language: Optional[Text],
        out_modality: Text,
        out_ids: List[Text],
        eval_size: float,
    ) -> E2eSearch:
        """Create a E2eSearch object with the provided information.

        Args:
            name (Text): Name of the E2eSearch.
            dataset (Dataset): Dataset to train and evaluate the bootstrapped models.
            in_language (Text): language of the input
            in_modality (Text): modality of the input
            in_ids (List[Text]): list of input columns Ids
            out_language (Text): language of the output
            out_modality (Text): modality of the output
            out_ids (List[Text]): list of output columns Ids
            eval_size (float): percentage of evalset.
        Returns:
            E2eSearch: The E2eSearch object created with the provided information or None if there was an error.
        """
        payload = {}
        assert eval_size > 0, f"Create E2eSearch: Train percentage ({eval_size}) must be greater than zero"
        assert eval_size <= 0.2, f"Create E2eSearch: Train percentage ({eval_size}) must be lower than or equal to 0.2"
        if isinstance(dataset, str) is True:
            dataset = DatasetFactory.get(dataset_id=dataset)
        
        try:
            url = urljoin(cls.backend_url, f"sdk/e2eSearch/cost-estimation")
            headers = {"Authorization": f"Token {config.TEAM_API_KEY}", "Content-Type": "application/json"}
            
            payload = {
                "dataset": {
                        "dataset_id": dataset.id,
                        "in_ids": in_ids,
                        "out_ids": out_ids,
                        "eval_size": eval_size
                    },
                "modality": {
                    "in_modality": in_modality,
                    "out_modality": out_modality,
                }
            }
            
            logging.info(f"Start service for POST Create E2eSearch - {url} - {headers} - {json.dumps(payload)}")
            r = _request_with_retry("post", url, headers=headers, json=payload)
            resp = r.json()
            logging.info(f"Response for POST Create E2eSearch - Status {resp}")
            cost = cls._create_cost_from_response(resp)
            return E2eSearch(
                name,
                dataset,
                cost,
                in_language,
                in_modality,
                in_ids,
                out_language,
                out_modality,
                out_ids,
                eval_size,
            )
        except Exception:
            error_message = f"Create E2eSearch: Error with payload {json.dumps(payload)}"
            logging.exception(error_message)
            return None
