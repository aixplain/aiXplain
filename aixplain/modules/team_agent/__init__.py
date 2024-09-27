__author__ = "aiXplain"

"""
Copyright 2024 The aiXplain SDK authors

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

     http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

Author: Lucas Pavanelli and Thiago Castro Ferreira
Date: August 15th 2024
Description:
    Team Agent Class
"""

import json
import logging
import time
import traceback

from aixplain.utils.file_utils import _request_with_retry
from aixplain.enums.supplier import Supplier
from aixplain.enums.asset_status import AssetStatus
from aixplain.enums.storage_type import StorageType
from aixplain.modules.model import Model
from aixplain.modules.agent import Agent
from typing import Dict, List, Text, Optional, Union
from urllib.parse import urljoin

from aixplain.utils import config


class TeamAgent(Model):
    """Advanced AI system capable of using multiple agents to perform a variety of tasks.

    Attributes:
        id (Text): ID of the Team Agent
        name (Text): Name of the Team Agent
        agents (List[Agent]): List of Agents that the Team Agent uses.
        description (Text, optional): description of the Team Agent. Defaults to "".
        llm_id (Text, optional): large language model. Defaults to GPT-4o (6646261c6eb563165658bbb1).
        supplier (Text): Supplier of the Team Agent.
        version (Text): Version of the Team Agent.
        backend_url (str): URL of the backend.
        api_key (str): The TEAM API key used for authentication.
        cost (Dict, optional): model price. Defaults to None.
        use_mentalist_and_inspector (bool): Use Mentalist and Inspector tools. Defaults to True.
    """

    def __init__(
        self,
        id: Text,
        name: Text,
        agents: List[Agent] = [],
        description: Text = "",
        llm_id: Text = "6646261c6eb563165658bbb1",
        api_key: Optional[Text] = config.TEAM_API_KEY,
        supplier: Union[Dict, Text, Supplier, int] = "aiXplain",
        version: Optional[Text] = None,
        cost: Optional[Dict] = None,
        use_mentalist_and_inspector: bool = True,
        status: AssetStatus = AssetStatus.ONBOARDING,
        **additional_info,
    ) -> None:
        """Create a FineTune with the necessary information.

        Args:
            id (Text): ID of the Team Agent
            name (Text): Name of the Team Agent
            agents (List[Agent]): List of agents that the Team Agent uses.
            description (Text, optional): description of the Team Agent. Defaults to "".
            llm_id (Text, optional): large language model. Defaults to GPT-4o (6646261c6eb563165658bbb1).
            supplier (Text): Supplier of the Team Agent.
            version (Text): Version of the Team Agent.
            backend_url (str): URL of the backend.
            api_key (str): The TEAM API key used for authentication.
            cost (Dict, optional): model price. Defaults to None.
            use_mentalist_and_inspector (bool): Use Mentalist and Inspector tools. Defaults to True.
        """
        super().__init__(id, name, description, api_key, supplier, version, cost=cost)
        self.additional_info = additional_info
        self.agents = agents
        self.llm_id = llm_id
        self.use_mentalist_and_inspector = use_mentalist_and_inspector
        if isinstance(status, str):
            try:
                status = AssetStatus(status)
            except Exception:
                status = AssetStatus.ONBOARDING
        self.status = status

    def run(
        self,
        data: Optional[Union[Dict, Text]] = None,
        query: Optional[Text] = None,
        session_id: Optional[Text] = None,
        history: Optional[List[Dict]] = None,
        name: Text = "model_process",
        timeout: float = 300,
        parameters: Dict = {},
        wait_time: float = 0.5,
        content: Optional[Union[Dict[Text, Text], List[Text]]] = None,
    ) -> Dict:
        """Runs a team agent call.

        Args:
            data (Optional[Union[Dict, Text]], optional): data to be processed by the team agent. Defaults to None.
            query (Optional[Text], optional): query to be processed by the team agent. Defaults to None.
            session_id (Optional[Text], optional): conversation Session ID. Defaults to None.
            history (Optional[List[Dict]], optional): chat history (in case session ID is None). Defaults to None.
            name (Text, optional): ID given to a call. Defaults to "model_process".
            timeout (float, optional): total polling time. Defaults to 300.
            parameters (Dict, optional): optional parameters to the model. Defaults to "{}".
            wait_time (float, optional): wait time in seconds between polling calls. Defaults to 0.5.
            content (Union[Dict[Text, Text], List[Text]], optional): Content inputs to be processed according to the query. Defaults to None.

        Returns:
            Dict: parsed output from model
        """
        start = time.time()
        try:
            response = self.run_async(
                data=data,
                query=query,
                session_id=session_id,
                history=history,
                name=name,
                parameters=parameters,
                content=content,
            )
            if response["status"] == "FAILED":
                end = time.time()
                response["elapsed_time"] = end - start
                return response
            poll_url = response["url"]
            end = time.time()
            response = self.sync_poll(poll_url, name=name, timeout=timeout, wait_time=wait_time)
            return response
        except Exception as e:
            msg = f"Error in request for {name} - {traceback.format_exc()}"
            logging.error(f"Team Agent Run: Error in running for {name}: {e}")
            end = time.time()
            return {"status": "FAILED", "error": msg, "elapsed_time": end - start}

    def run_async(
        self,
        data: Optional[Union[Dict, Text]] = None,
        query: Optional[Text] = None,
        session_id: Optional[Text] = None,
        history: Optional[List[Dict]] = None,
        name: Text = "model_process",
        parameters: Dict = {},
        content: Optional[Union[Dict[Text, Text], List[Text]]] = None,
    ) -> Dict:
        """Runs asynchronously a Team Agent call.

        Args:
            data (Optional[Union[Dict, Text]], optional): data to be processed by the Team Agent. Defaults to None.
            query (Optional[Text], optional): query to be processed by the Team Agent. Defaults to None.
            session_id (Optional[Text], optional): conversation Session ID. Defaults to None.
            history (Optional[List[Dict]], optional): chat history (in case session ID is None). Defaults to None.
            name (Text, optional): ID given to a call. Defaults to "model_process".
            parameters (Dict, optional): optional parameters to the model. Defaults to "{}".
            content (Union[Dict[Text, Text], List[Text]], optional): Content inputs to be processed according to the query. Defaults to None.

        Returns:
            dict: polling URL in response
        """
        from aixplain.factories.file_factory import FileFactory

        assert data is not None or query is not None, "Either 'data' or 'query' must be provided."
        if data is not None:
            if isinstance(data, dict):
                assert "query" in data and data["query"] is not None, "When providing a dictionary, 'query' must be provided."
                query = data.get("query")
                if session_id is None:
                    session_id = data.get("session_id")
                if history is None:
                    history = data.get("history")
                if content is None:
                    content = data.get("content")
            else:
                query = data

        # process content inputs
        if content is not None:
            assert FileFactory.check_storage_type(query) == StorageType.TEXT, "When providing 'content', query must be text."

            if isinstance(content, list):
                assert len(content) <= 3, "The maximum number of content inputs is 3."
                for input_link in content:
                    input_link = FileFactory.to_link(input_link)
                    query += f"\n{input_link}"
            elif isinstance(content, dict):
                for key, value in content.items():
                    assert "{{" + key + "}}" in query, f"Key '{key}' not found in query."
                    value = FileFactory.to_link(value)
                    query = query.replace("{{" + key + "}}", f"'{value}'")

        headers = {"x-api-key": self.api_key, "Content-Type": "application/json"}

        payload = {"id": self.id, "query": FileFactory.to_link(query), "sessionId": session_id, "history": history}
        payload.update(parameters)
        payload = json.dumps(payload)

        r = _request_with_retry("post", self.url, headers=headers, data=payload)
        logging.info(f"Team Agent Run Async: Start service for {name} - {self.url} - {payload} - {headers}")

        resp = None
        try:
            resp = r.json()
            logging.info(f"Result of request for {name} - {r.status_code} - {resp}")

            poll_url = resp["data"]
            response = {"status": "IN_PROGRESS", "url": poll_url}
        except Exception:
            response = {"status": "FAILED"}
            msg = f"Error in request for {name} - {traceback.format_exc()}"
            logging.error(f"Team Agent Run Async: Error in running for {name}: {resp}")
            if resp is not None:
                response["error"] = msg
        return response

    def delete(self) -> None:
        """Delete Corpus service"""
        try:
            url = urljoin(config.BACKEND_URL, f"sdk/agent-communities/{self.id}")
            headers = {"x-api-key": config.TEAM_API_KEY, "Content-Type": "application/json"}
            logging.debug(f"Start service for DELETE Team Agent  - {url} - {headers}")
            r = _request_with_retry("delete", url, headers=headers)
            if r.status_code != 200:
                raise Exception()
        except Exception:
            message = (
                f"Team Agent Deletion Error (HTTP {r.status_code}): Make sure the Team Agent exists and you are the owner."
            )
            logging.error(message)
            raise Exception(f"{message}")
