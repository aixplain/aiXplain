"""Copyright 2024 The aiXplain SDK authors.

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
import warnings
from typing import Dict, List, Optional, Text, Union
from urllib.parse import urljoin

from aixplain.enums.supplier import Supplier
from aixplain.modules.agent import Agent
from aixplain.modules.team_agent import TeamAgent
from aixplain.utils import config
from aixplain.factories.team_agent_factory.utils import build_team_agent
from aixplain.utils.convert_datatype_utils import normalize_expected_output
from aixplain.utils.request_utils import _request_with_retry
from aixplain.modules.model.llm_model import LLM
from aixplain.utils.llm_utils import get_llm_instance
from pydantic import BaseModel
from aixplain.modules.agent.output_format import OutputFormat


class TeamAgentFactory:
    """Factory class for creating and managing team agents.

    This class provides functionality for creating new team agents, retrieving existing
    team agents, and managing team agent configurations in the aiXplain platform.
    Team agents can be composed of multiple individual agents, LLMs
    working together to accomplish complex tasks.
    """

    @classmethod
    def create(
        cls,
        name: Text,
        agents: List[Union[Text, Agent]],
        llm: Optional[Union[LLM, Text]] = None,
        supervisor_llm: Optional[Union[LLM, Text]] = None,
        description: Text = "",
        api_key: Text = config.TEAM_API_KEY,
        supplier: Union[Dict, Text, Supplier, int] = "aiXplain",
        version: Optional[Text] = None,
        instructions: Optional[Text] = None,
        output_format: Optional[OutputFormat] = None,
        expected_output: Optional[Union[BaseModel, Text, dict]] = None,
        **kwargs,
    ) -> TeamAgent:
        """Create a new team agent in the platform.

        Args:
            name: The name of the team agent.
            agents: A list of agents to be added to the team.
            llm (Optional[Union[LLM, Text]], optional): The LLM to be used for the team agent.
            supervisor_llm (Optional[Union[LLM, Text]], optional): Main supervisor LLM. Defaults to None.
            description: The description of the team agent to be displayed in the aiXplain platform.
            api_key: The API key to be used for the team agent.
            supplier: The supplier of the team agent.
            version: The version of the team agent.
            instructions: The instructions to guide the team agent (i.e. appended in the prompt of the team agent).
            output_format: The output format to be used for the team agent.
            expected_output: The expected output to be used for the team agent.
            **kwargs: Additional keyword arguments for backward compatibility (deprecated parameters).

        Returns:
            A new team agent instance.

        Deprecated Args:
            llm_id: DEPRECATED. Use 'llm' parameter instead. The ID of the LLM to be used for the team agent.
            mentalist_llm: DEPRECATED. LLM for planning.
            use_mentalist: DEPRECATED. Whether to use the mentalist agent.
        """
        # Define supported kwargs
        supported_kwargs = {
            "llm_id",
            "mentalist_llm",
            "use_mentalist",
            "use_mentalist_and_inspector",
            "use_inspector",
            "num_inspectors",
        }

        # Validate kwargs - raise error if unsupported kwargs are provided
        unsupported_kwargs = set(kwargs.keys()) - supported_kwargs
        if unsupported_kwargs:
            raise ValueError(
                f"Unsupported keyword argument(s): {', '.join(sorted(unsupported_kwargs))}. "
                f"Supported kwargs are: {', '.join(sorted(supported_kwargs))}."
            )
        # Handle deprecated parameters from kwargs
        if "llm_id" in kwargs:
            llm_id = kwargs.pop("llm_id")
            warnings.warn(
                "Parameter 'llm_id' is deprecated and will be removed in a future version. "
                "Please use 'llm' parameter instead.",
                DeprecationWarning,
                stacklevel=2,
            )
        else:
            llm_id = "669a63646eb56306647e1091"

        if "mentalist_llm" in kwargs:
            mentalist_llm = kwargs.pop("mentalist_llm")
            warnings.warn(
                "Parameter 'mentalist_llm' is deprecated and will be removed in a future version.",
                DeprecationWarning,
                stacklevel=2,
            )
        else:
            mentalist_llm = None

        if "use_mentalist" in kwargs:
            use_mentalist = kwargs.pop("use_mentalist")
            warnings.warn(
                "Parameter 'use_mentalist' is deprecated and will be removed in a future version.",
                DeprecationWarning,
                stacklevel=2,
            )
        else:
            use_mentalist = True

        # legacy params
        if "use_mentalist_and_inspector" in kwargs:
            logging.warning(
                "TeamAgent Onboarding Warning: use_mentalist_and_inspector is no longer supported. Use use_mentalist and inspectors instead."
            )
        if "use_inspector" in kwargs:
            logging.warning(
                "TeamAgent Onboarding Warning: use_inspector is no longer supported. Inspectors are no longer supported on v1."
            )
        if "num_inspectors" in kwargs:
            logging.warning(
                "TeamAgent Onboarding Warning: num_inspectors is no longer supported. Inspectors are no longer supported on v1."
            )

        assert len(agents) > 0, "TeamAgent Onboarding Error: At least one agent must be provided."

        if output_format == OutputFormat.JSON:
            assert expected_output is not None and (
                issubclass(expected_output, BaseModel) or isinstance(expected_output, dict)
            ), "'expected_output' must be a Pydantic BaseModel or a JSON object when 'output_format' is JSON."

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

        def _get_llm_safely(llm_id: str, llm_type: str) -> LLM:
            """Helper to safely get an LLM instance with consistent error handling."""
            try:
                return get_llm_instance(llm_id, api_key=api_key)
            except Exception:
                raise Exception(
                    f"TeamAgent Onboarding Error: LLM {llm_id} does not exist for {llm_type}. To resolve this, set the following LLM parameters to a valid LLM object or LLM ID: llm, supervisor_llm, mentalist_llm."
                )

        def _setup_llm_and_tool(
            llm_param: Optional[Union[LLM, Text]], default_id: Text, llm_type: str, description: str, tools: List[Dict]
        ) -> LLM:
            """Helper to set up an LLM and add its tool configuration."""
            llm_instance = None
            # Set up LLM
            if llm_param is None:
                llm_instance = _get_llm_safely(default_id, llm_type)
            else:
                llm_instance = _get_llm_safely(llm_param, llm_type) if isinstance(llm_param, str) else llm_param

            # Add tool configuration
            if llm_instance is not None:
                tools.append(
                    {
                        "type": "llm",
                        "description": description,
                        "parameters": llm_instance.get_parameters().to_list()
                        if llm_instance.get_parameters()
                        else None,
                    }
                )
            return llm_instance, tools

        # Set up LLMs and their tools
        tools = []
        llm, tools = _setup_llm_and_tool(llm, llm_id, "Main LLM", "main", tools)
        supervisor_llm, tools = _setup_llm_and_tool(supervisor_llm, llm_id, "Supervisor LLM", "supervisor", tools)
        mentalist_llm, tools = (
            _setup_llm_and_tool(mentalist_llm, llm_id, "Mentalist LLM", "mentalist", tools)
            if use_mentalist
            else (None, [])
        )

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
            "llmId": llm.id,
            "supervisorId": supervisor_llm.id,
            "plannerId": mentalist_llm.id if use_mentalist else None,
            "supplier": supplier,
            "version": version,
            "status": "draft",
            "tools": tools,
            "instructions": instructions,
        }
        # Store the LLM objects directly in the payload for build_team_agent
        internal_payload = payload.copy()
        if llm is not None:
            internal_payload["llm"] = llm
        if supervisor_llm is not None:
            internal_payload["supervisor_llm"] = supervisor_llm
        if mentalist_llm is not None:
            internal_payload["mentalist_llm"] = mentalist_llm
        if expected_output:
            payload["expectedOutput"] = normalize_expected_output(expected_output)
        if output_format:
            if isinstance(output_format, OutputFormat):
                output_format = output_format.value
            payload["outputFormat"] = output_format

        team_agent = build_team_agent(payload=internal_payload, agents=agent_list, api_key=api_key)
        team_agent.validate(raise_exception=True)
        response = "Unspecified error"
        try:
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
    def create_from_dict(cls, dict: Dict) -> TeamAgent:
        """Create a team agent from a dictionary representation.

        This method instantiates a TeamAgent object from a dictionary containing
        the agent's configuration.

        Args:
            dict (Dict): Dictionary containing team agent configuration including:
                - id: Team agent identifier
                - name: Team agent name
                - agents: List of agent configurations
                - llm: Optional LLM configuration
                - supervisor_llm: Optional supervisor LLM configuration
                - mentalist_llm: Optional mentalist LLM configuration

        Returns:
            TeamAgent: Instantiated team agent with validated configuration.

        Raises:
            Exception: If validation fails or required fields are missing.
        """
        team_agent = TeamAgent.from_dict(dict)
        team_agent.validate(raise_exception=True)
        team_agent.url = urljoin(config.BACKEND_URL, f"sdk/agent-communities/{team_agent.id}/run")
        return team_agent

    @classmethod
    def list(cls) -> Dict:
        """List all team agents available in the platform.

        This method retrieves all team agents accessible to the current user,
        using the configured API key.

        Returns:
            Dict: Response containing:
                - results (List[TeamAgent]): List of team agent objects
                - page_total (int): Total items in current page
                - page_number (int): Current page number (always 0)
                - total (int): Total number of team agents

        Raises:
            Exception: If the request fails or returns an error, including cases
                where authentication fails or the service is unavailable.
        """
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
                try:
                    team_agent_ = build_team_agent(agent)
                    agents.append(team_agent_)
                except Exception:
                    logging.warning(f"There was an error building the team agent {agent['name']}. Skipping...")
                    continue
            return {"results": agents, "page_total": page_total, "page_number": 0, "total": total}
        else:
            error_msg = "Agent Listing Error: Please contact the administrators."
            if isinstance(resp, dict) and "message" in resp:
                msg = resp["message"]
                error_msg = f"Agent Listing Error (HTTP {r.status_code}): {msg}"
            logging.exception(error_msg)
            raise Exception(error_msg)

    @classmethod
    def get(
        cls, agent_id: Optional[Text] = None, name: Optional[Text] = None, api_key: Optional[Text] = None
    ) -> TeamAgent:
        """Retrieve a team agent by its ID or name.

        This method fetches a specific team agent from the platform using its
        unique identifier or name.

        Args:
            agent_id (Optional[Text], optional): Unique identifier of the team agent to retrieve.
            name (Optional[Text], optional): Name of the team agent to retrieve.
            api_key (Optional[Text], optional): API key for authentication.
                Defaults to None, using the configured TEAM_API_KEY.

        Returns:
            TeamAgent: Retrieved team agent with its full configuration.

        Raises:
            Exception: If:
                - Team agent ID/name is invalid
                - Authentication fails
                - Service is unavailable
                - Other API errors occur
            ValueError: If neither agent_id nor name is provided, or if both are provided.
        """
        # Validate that exactly one parameter is provided
        if not (agent_id or name) or (agent_id and name):
            raise ValueError("Must provide exactly one of 'agent_id' or 'name'")

        # Construct URL based on parameter type
        if agent_id:
            url = urljoin(config.BACKEND_URL, f"sdk/agent-communities/{agent_id}")
        else:  # name is provided
            url = urljoin(config.BACKEND_URL, f"sdk/agent-communities/by-name/{name}")

        api_key = api_key if api_key is not None else config.TEAM_API_KEY
        headers = {"x-api-key": api_key, "Content-Type": "application/json"}
        logging.info(f"Start service for GET Team Agent - {url} - {headers}")
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
