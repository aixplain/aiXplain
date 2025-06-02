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
from typing import Dict, List, Optional, Text, Union
from urllib.parse import urljoin

from aixplain.enums.supplier import Supplier
from aixplain.modules.agent import Agent
from aixplain.modules.team_agent import TeamAgent, InspectorTarget
from aixplain.modules.team_agent.inspector import Inspector
from aixplain.utils import config
from aixplain.factories.team_agent_factory.utils import build_team_agent
from aixplain.utils.request_utils import _request_with_retry
from aixplain.modules.model.llm_model import LLM
from aixplain.utils.llm_utils import get_llm_instance


class TeamAgentFactory:
    @classmethod
    def create(
        cls,
        name: Text,
        agents: List[Union[Text, Agent]],
        llm_id: Text = "669a63646eb56306647e1091",
        llm: Optional[Union[LLM, Text]] = None,
        supervisor_llm: Optional[Union[LLM, Text]] = None,
        mentalist_llm: Optional[Union[LLM, Text]] = None,
        description: Text = "",
        api_key: Text = config.TEAM_API_KEY,
        supplier: Union[Dict, Text, Supplier, int] = "aiXplain",
        version: Optional[Text] = None,
        use_mentalist: bool = True,
        inspectors: List[Inspector] = [],
        inspector_targets: List[Union[InspectorTarget, Text]] = [InspectorTarget.STEPS],
        instructions: Optional[Text] = None,
        **kwargs,
    ) -> TeamAgent:
        """Create a new team agent in the platform.

        Args:
            name: The name of the team agent.
            agents: A list of agents to be added to the team.
            llm_id: The ID of the LLM to be used for the team agent.
            llm (Optional[Union[LLM, Text]], optional): The LLM to be used for the team agent.
            supervisor_llm (Optional[Union[LLM, Text]], optional): Main supervisor LLM. Defaults to None.
            mentalist_llm (Optional[Union[LLM, Text]], optional): LLM for planning. Defaults to None.
            description: The description of the team agent to be displayed in the aiXplain platform.
            api_key: The API key to be used for the team agent.
            supplier: The supplier of the team agent.
            version: The version of the team agent.
            use_mentalist: Whether to use the mentalist agent.
            inspectors: A list of inspectors to be added to the team.
            inspector_targets: Which stages to be inspected during an execution of the team agent. (steps, output)
            use_mentalist_and_inspector: Whether to use the mentalist and inspector agents. (legacy)
            instructions: The instructions to guide the team agent (i.e. appended in the prompt of the team agent).

        Returns:
            A new team agent instance.
        """
        # legacy params
        if "use_mentalist_and_inspector" in kwargs:
            logging.warning(
                "TeamAgent Onboarding Warning: use_mentalist_and_inspector is no longer supported. Use use_mentalist and inspectors instead."
            )
        if "use_inspector" in kwargs:
            logging.warning("TeamAgent Onboarding Warning: use_inspector is no longer supported. Use inspectors instead.")
        if "num_inspectors" in kwargs:
            logging.warning("TeamAgent Onboarding Warning: num_inspectors is no longer supported. Use inspectors instead.")

        assert len(agents) > 0, "TeamAgent Onboarding Error: At least one agent must be provided."
        agent_list = []
        for agent in agents:
            if isinstance(agent, Text) is True:
                try:
                    from aixplain.factories.agent_factory import AgentFactory

                    agent_obj = AgentFactory.get(agent)
                except Exception:
                    raise Exception(f"TeamAgent Onboarding Error: Agent {agent} does not exist.")
            else:
                from aixplain.modules.agent import Agent

                agent_obj = agent

                assert isinstance(agent, Agent), "TeamAgent Onboarding Error: Agents must be instances of Agent class"
            agent_list.append(agent_obj)

        if inspectors:
            try:
                # convert to enum if string and check its validity
                inspector_targets = [InspectorTarget(target) for target in inspector_targets]
            except ValueError:
                raise ValueError(
                    f"TeamAgent Onboarding Error: Invalid inspector target. Valid targets are: {list(InspectorTarget)}"
                )

            if not use_mentalist:
                raise Exception("TeamAgent Onboarding Error: To use the Inspector agent, you must enable Mentalist.")
        else:
            inspector_targets = []

        mentalist_llm_id = llm_id if use_mentalist else None

        # Set up LLMs
        if llm is None:
            llm = get_llm_instance(llm_id, api_key=api_key)

        if supervisor_llm is None:
            supervisor_llm = get_llm_instance(llm_id, api_key=api_key)

        if use_mentalist and mentalist_llm is None:
            mentalist_llm = get_llm_instance(mentalist_llm_id or "669a63646eb56306647e1091", api_key=api_key)

        team_agent = None
        url = urljoin(config.BACKEND_URL, "sdk/agent-communities")
        headers = {"x-api-key": api_key}

        if isinstance(supplier, dict):
            supplier = supplier["code"]
        elif isinstance(supplier, Supplier):
            supplier = supplier.value["code"]

        agent_payload_list = []
        for idx, agent in enumerate(agents):
            agent_payload_list.append({"assetId": agent.id, "number": idx, "type": "AGENT", "label": "AGENT"})

        payload = {
            "name": name,
            "agents": agent_payload_list,
            "links": [],
            "description": description,
            "llmId": llm.id if llm else llm_id,
            "supervisorId": supervisor_llm.id if supervisor_llm else llm_id,
            "plannerId": mentalist_llm.id if mentalist_llm else mentalist_llm_id,
            "inspectors": inspectors,
            "inspectorTargets": inspector_targets,
            "supplier": supplier,
            "version": version,
            "status": "draft",
            "tools": [],
            "role": instructions,
        }

        # Add LLM tools to the payload
        if llm is not None:
            llm = get_llm_instance(llm, api_key=api_key) if isinstance(llm, str) else llm
            payload["tools"].append(
                {
                    "type": "llm",
                    "description": "main",
                    "parameters": llm.get_parameters().to_list() if llm.get_parameters() else None,
                }
            )

        if supervisor_llm is not None:
            supervisor_llm = (
                get_llm_instance(supervisor_llm, api_key=api_key) if isinstance(supervisor_llm, str) else supervisor_llm
            )
            payload["tools"].append(
                {
                    "type": "llm",
                    "description": "supervisor",
                    "parameters": supervisor_llm.get_parameters().to_list() if supervisor_llm.get_parameters() else None,
                }
            )

        if mentalist_llm is not None:
            mentalist_llm = (
                get_llm_instance(mentalist_llm, api_key=api_key) if isinstance(mentalist_llm, str) else mentalist_llm
            )
            payload["tools"].append(
                {
                    "type": "llm",
                    "description": "mentalist",
                    "parameters": mentalist_llm.get_parameters().to_list() if mentalist_llm.get_parameters() else None,
                }
            )

        # Store the LLM objects directly in the payload for build_team_agent
        internal_payload = payload.copy()
        if llm is not None:
            internal_payload["llm"] = llm
        if supervisor_llm is not None:
            internal_payload["supervisor_llm"] = supervisor_llm
        if mentalist_llm is not None:
            internal_payload["mentalist_llm"] = mentalist_llm

        team_agent = build_team_agent(payload=internal_payload, agents=agent_list, api_key=api_key)
        team_agent.validate(raise_exception=True)
        response = "Unspecified error"
        try:
            payload["inspectors"] = [
                inspector.model_dump(by_alias=True) for inspector in inspectors
            ]  # convert Inspector object to dict
            logging.debug(f"Start service for POST Create TeamAgent  - {url} - {headers} - {json.dumps(payload)}")
            r = _request_with_retry("post", url, headers=headers, json=payload)
            response = r.json()
        except Exception as e:
            raise Exception(e)

        if 200 <= r.status_code < 300:
            # Preserve the LLM objects
            if "llm" in internal_payload:
                response["llm"] = internal_payload["llm"]
            if "supervisor_llm" in internal_payload:
                response["supervisor_llm"] = internal_payload["supervisor_llm"]
            if "mentalist_llm" in internal_payload:
                response["mentalist_llm"] = internal_payload["mentalist_llm"]

            team_agent = build_team_agent(payload=response, agents=agent_list, api_key=api_key)
        else:
            error_msg = f"{response}"
            if "message" in response:
                msg = response["message"]
                if response["message"] == "err.name_already_exists":
                    msg = "TeamAgent name already exists."
                elif response["message"] == "err.asset_is_not_available":
                    msg = "Some tools are not available."
                error_msg = f"TeamAgent Onboarding Error (HTTP {r.status_code}): {msg}"
            logging.exception(error_msg)
            raise Exception(error_msg)
        return team_agent

    @classmethod
    def list(cls) -> Dict:
        """List all agents available in the platform."""
        url = urljoin(config.BACKEND_URL, "sdk/agent-communities")
        headers = {"x-api-key": config.TEAM_API_KEY, "Content-Type": "application/json"}

        resp = {}
        payload = {}
        logging.info(f"Start service for GET List Agents - {url} - {headers} - {json.dumps(payload)}")
        try:
            r = _request_with_retry("get", url, headers=headers)
            resp = r.json()
        except Exception:
            raise Exception("Team Agent Listing Error: Please contact the administrators.")

        if 200 <= r.status_code < 300:
            agents, page_total, total = [], 0, 0
            results = resp
            page_total = len(results)
            total = len(results)
            logging.info(f"Response for GET List Agents - Page Total: {page_total} / Total: {total}")
            for agent in results:
                agents.append(build_team_agent(agent))
            return {"results": agents, "page_total": page_total, "page_number": 0, "total": total}
        else:
            error_msg = "Agent Listing Error: Please contact the administrators."
            if isinstance(resp, dict) and "message" in resp:
                msg = resp["message"]
                error_msg = f"Agent Listing Error (HTTP {r.status_code}): {msg}"
            logging.exception(error_msg)
            raise Exception(error_msg)

    @classmethod
    def get(cls, agent_id: Text, api_key: Optional[Text] = None) -> TeamAgent:
        """Get agent by id."""
        url = urljoin(config.BACKEND_URL, f"sdk/agent-communities/{agent_id}")
        api_key = api_key if api_key is not None else config.TEAM_API_KEY
        headers = {"x-api-key": api_key, "Content-Type": "application/json"}
        logging.info(f"Start service for GET Team Agent  - {url} - {headers}")
        try:
            r = _request_with_retry("get", url, headers=headers)
            resp = r.json()
        except Exception:
            raise Exception("Team Agent Get Error: Please contact the administrators.")

        if 200 <= r.status_code < 300:
            return build_team_agent(resp)
        else:
            msg = "Please contact the administrators."
            if "message" in resp:
                msg = resp["message"]
            error_msg = f"Team Agent Get Error (HTTP {r.status_code}): {msg}"
            raise Exception(error_msg)
