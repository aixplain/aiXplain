__author__ = "lucaspavanelli"

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

Author: Thiago Castro Ferreira and Lucas Pavanelli
Date: August 15th 2024
Description:
    TeamAgent Factory Class
"""

import json
import logging

from aixplain.enums.supplier import Supplier
from aixplain.modules.agent import Agent
from aixplain.modules.team_agent import TeamAgent
from aixplain.utils import config
from typing import Dict, List, Optional, Text, Union

from aixplain.factories.team_agent_factory.utils import build_team_agent
from aixplain.utils.file_utils import _request_with_retry
from urllib.parse import urljoin


class TeamAgentFactory:
    @classmethod
    def create(
        cls,
        name: Text,
        agents: List[Agent],
        llm_id: Text = "669a63646eb56306647e1091",
        description: Text = "",
        api_key: Text = config.TEAM_API_KEY,
        supplier: Union[Dict, Text, Supplier, int] = "aiXplain",
        version: Optional[Text] = None,
    ) -> TeamAgent:
        """Create a new team agent in the platform."""
        assert len(agents) > 0, "TeamAgent Onboarding Error: At least one agent must be provided."
        for agent in agents:
            assert isinstance(agent, Agent), "TeamAgent Onboarding Error: Agents must be instances of Agent class"
            assert agent.plann, "TeamAgent Onboarding Error: Agents must have the same LLM ID"
        try:
            team_agent = None
            url = urljoin(config.BACKEND_URL, "sdk/agent-communities")
            headers = {"x-api-key": api_key}

            if isinstance(supplier, dict):
                supplier = supplier["code"]
            elif isinstance(supplier, Supplier):
                supplier = supplier.value["code"]

            payload = {
                "name": name,
                "agents": agents,
                "links": [],
                "description": description,
                "llm_id": llm_id,
                "supervisorId": llm_id,
                "plannerId": llm_id,
                "supplier": supplier,
                "version": version,
            }

            logging.info(f"Start service for POST Create TeamAgent  - {url} - {headers} - {json.dumps(payload)}")
            r = _request_with_retry("post", url, headers=headers, json=payload)
            if 200 <= r.status_code < 300:
                response = r.json()
                team_agent = build_team_agent(payload=response, api_key=api_key)
            else:
                error = r.json()
                error_msg = "TeamAgent Onboarding Error: Please contact the administrators."
                if "message" in error:
                    msg = error["message"]
                    if error["message"] == "err.name_already_exists":
                        msg = "TeamAgent name already exists."
                    elif error["message"] == "err.asset_is_not_available":
                        msg = "Some tools are not available."
                    error_msg = f"TeamAgent Onboarding Error (HTTP {r.status_code}): {msg}"
                logging.exception(error_msg)
                raise Exception(error_msg)
        except Exception as e:
            raise Exception(e)
        return team_agent
