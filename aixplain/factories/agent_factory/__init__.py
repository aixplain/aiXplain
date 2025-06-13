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
Date: May 16th 2024
Description:
    Agent Factory Class
"""

import json
import logging
import warnings
import os

from aixplain.enums.function import Function
from aixplain.enums.supplier import Supplier
from aixplain.modules.agent import Agent, AgentTask, Tool
from aixplain.modules.agent.tool.model_tool import ModelTool
from aixplain.modules.agent.tool.pipeline_tool import PipelineTool
from aixplain.modules.agent.tool.python_interpreter_tool import PythonInterpreterTool
from aixplain.modules.agent.tool.custom_python_code_tool import CustomPythonCodeTool
from aixplain.modules.agent.tool.sql_tool import (
    SQLTool,
)
from aixplain.modules.model import Model
from aixplain.modules.model.llm_model import LLM
from aixplain.modules.pipeline import Pipeline
from aixplain.utils import config
from typing import Callable, Dict, List, Optional, Text, Union

from aixplain.utils.request_utils import _request_with_retry
from urllib.parse import urljoin
from aixplain.enums import DatabaseSourceType


class AgentFactory:
    @classmethod
    def create(
        cls,
        name: Text,
        description: Text,
        instructions: Optional[Text] = None,
        llm: Optional[Union[LLM, Text]] = None,
        llm_id: Optional[Text] = None,
        tools: List[Union[Tool, Model]] = [],
        api_key: Text = config.TEAM_API_KEY,
        supplier: Union[Dict, Text, Supplier, int] = "aiXplain",
        version: Optional[Text] = None,
        tasks: List[AgentTask] = [],
    ) -> Agent:
        """Create a new agent in the platform.

        Warning:
            The 'instructions' parameter was recently added and serves the same purpose as 'description' did previously: set the role of the agent as a system prompt.
            The 'description' parameter is still required and should be used to set a short summary of the agent's purpose.
            For the next releases, the 'instructions' parameter will be required.

        Args:
            name (Text): name of the agent
            description (Text): description of the agent role.
            instructions (Text): role of the agent.
            llm (Optional[Union[LLM, Text]], optional): LLM instance to use as an object or as an ID.
            llm_id (Optional[Text], optional): ID of LLM to use if no LLM instance provided. Defaults to None.
            tools (List[Union[Tool, Model]], optional): list of tool for the agent. Defaults to [].
            api_key (Text, optional): team/user API key. Defaults to config.TEAM_API_KEY.
            supplier (Union[Dict, Text, Supplier, int], optional): owner of the agent. Defaults to "aiXplain".
            version (Optional[Text], optional): version of the agent. Defaults to None.
            tasks (List[AgentTask], optional): list of tasks for the agent. Defaults to [].

        Returns:
            Agent: created Agent
        """
        from aixplain.utils.llm_utils import get_llm_instance

        if llm is None and llm_id is not None:
            llm = get_llm_instance(llm_id, api_key=api_key)
        elif llm is None:
            # Use default GPT-4o if no LLM specified
            llm = get_llm_instance("669a63646eb56306647e1091", api_key=api_key)

        if instructions is None:
            warnings.warn(
                "Use `instructions` to define the **system prompt**. "
                "Use `description` to provide a **short summary** of the agent for metadata and dashboard display. "
                "Note: In upcoming releases, `instructions` will become a required parameter.",
                UserWarning,
            )
        warnings.warn(
            "Use `llm` to define the large language model (aixplain.modules.model.llm_model.LLM) to be used as agent. "
            "Use `llm_id` to provide the model ID of the large language model to be used as agent. "
            "Note: In upcoming releases, `llm` will become a required parameter.",
            UserWarning,
        )
        from aixplain.factories.agent_factory.utils import build_agent, build_tool_payload

        agent = None
        url = urljoin(config.BACKEND_URL, "sdk/agents")
        headers = {"x-api-key": api_key}

        if isinstance(supplier, dict):
            supplier = supplier["code"]
        elif isinstance(supplier, Supplier):
            supplier = supplier.value["code"]

        payload = {
            "name": name,
            "assets": [build_tool_payload(tool) for tool in tools],
            "description": description,
            "role": instructions or description,
            "supplier": supplier,
            "version": version,
            "llmId": llm_id,
            "status": "draft",
            "tasks": [task.to_dict() for task in tasks],
            "tools": [],
        }

        if llm is not None:
            llm = get_llm_instance(llm, api_key=api_key) if isinstance(llm, str) else llm
            payload["tools"].append(
                {
                    "type": "llm",
                    "description": "main",
                    "parameters": llm.get_parameters().to_list() if llm.get_parameters() else None,
                }
            )
            payload["llmId"] = llm.id
            # Store the LLM object in payload to avoid recreating it
            payload["llm"] = llm

        agent = build_agent(payload=payload, tools=tools, api_key=api_key)
        agent.validate(raise_exception=True)
        response = "Unspecified error"
        try:
            logging.debug(f"Start service for POST Create Agent  - {url} - {headers} - {json.dumps(agent.to_dict())}")
            r = _request_with_retry("post", url, headers=headers, json=agent.to_dict())
            response = r.json()
        except Exception:
            raise Exception("Agent Onboarding Error: Please contact the administrators.")

        if 200 <= r.status_code < 300:
            # Preserve the LLM if it exists
            if "llm" in payload:
                response["llm"] = payload["llm"]
            agent = build_agent(payload=response, tools=tools, api_key=api_key)
        else:
            error_msg = f"Agent Onboarding Error: {response}"
            if "message" in response:
                msg = response["message"]
                if response["message"] == "err.name_already_exists":
                    msg = "Agent name already exists."
                elif response["message"] == "err.asset_is_not_available":
                    msg = "Some tools are not available."
                error_msg = f"Agent Onboarding Error (HTTP {r.status_code}): {msg}"
            logging.exception(error_msg)
            raise Exception(error_msg)
        return agent

    @classmethod
    def create_task(
        cls, name: Text, description: Text, expected_output: Text, dependencies: Optional[List[Text]] = None
    ) -> AgentTask:
        return AgentTask(name=name, description=description, expected_output=expected_output, dependencies=dependencies)

    @classmethod
    def create_model_tool(
        cls,
        model: Optional[Union[Model, Text]] = None,
        function: Optional[Union[Function, Text]] = None,
        supplier: Optional[Union[Supplier, Text]] = None,
        description: Text = "",
        parameters: Optional[Dict] = None,
        name: Optional[Text] = None,
    ) -> ModelTool:
        """Create a new model tool."""
        if function is not None and isinstance(function, str):
            function = Function(function)

        if supplier is not None:
            if isinstance(supplier, str):
                for supplier_ in Supplier:
                    if supplier.lower() in [supplier_.value["code"].lower(), supplier_.value["name"].lower()]:
                        supplier = supplier_
                        break
            assert isinstance(supplier, Supplier), f"Supplier {supplier} is not a valid supplier"
        return ModelTool(
            function=function, supplier=supplier, model=model, name=name, description=description, parameters=parameters
        )

    @classmethod
    def create_pipeline_tool(
        cls, description: Text, pipeline: Union[Pipeline, Text], name: Optional[Text] = None
    ) -> PipelineTool:
        """Create a new pipeline tool."""
        return PipelineTool(description=description, pipeline=pipeline, name=name)

    @classmethod
    def create_python_interpreter_tool(cls) -> PythonInterpreterTool:
        """Create a new python interpreter tool."""
        return PythonInterpreterTool()

    @classmethod
    def create_custom_python_code_tool(
        cls, code: Union[Text, Callable], name: Text, description: Text = ""
    ) -> CustomPythonCodeTool:
        """Create a new custom python code tool."""
        return CustomPythonCodeTool(name=name, description=description, code=code)

    @classmethod
    def create_sql_tool(
        cls,
        name: Text,
        description: Text,
        source: str,
        source_type: Union[str, DatabaseSourceType],
        schema: Optional[Text] = None,
        tables: Optional[List[Text]] = None,
        enable_commit: bool = False,
    ) -> SQLTool:
        """Create a new SQL tool

        Args:
            name (Text): name of the tool
            description (Text): description of the database tool
            source (Union[Text, Dict]): database source - can be a connection string or dictionary with connection details
            source_type (Union[str, DatabaseSourceType]): type of source (postgresql, sqlite, csv) or DatabaseSourceType enum
            schema (Optional[Text], optional): database schema description
            tables (Optional[List[Text]], optional): table names to work with (optional)
            enable_commit (bool, optional): enable to modify the database (optional)
        Returns:
            SQLTool: created SQLTool

        Examples:
            # CSV - Simple
            sql_tool = AgentFactory.create_sql_tool(
                description="My CSV Tool",
                source="/path/to/data.csv",
                source_type="csv",
                tables=["data"]
            )

            # SQLite - Simple
            sql_tool = AgentFactory.create_sql_tool(
                description="My SQLite Tool",
                source="/path/to/database.sqlite",
                source_type="sqlite",
                tables=["users", "products"]
            )
        """
        from aixplain.modules.agent.tool.sql_tool import (
            SQLToolError,
            create_database_from_csv,
            get_table_schema,
            get_table_names_from_schema,
        )

        if not source:
            raise SQLToolError("Source must be provided")
        if not source_type:
            raise SQLToolError("Source type must be provided")

        # Validate source type
        if isinstance(source_type, str):
            try:
                source_type = DatabaseSourceType.from_string(source_type)
            except ValueError as e:
                raise SQLToolError(str(e))
        elif isinstance(source_type, DatabaseSourceType):
            # Already the correct type, no conversion needed
            pass
        else:
            raise SQLToolError(f"Source type must be either a string or DatabaseSourceType enum, got {type(source_type)}")

        database_path = None  # Final database path to pass to SQLTool

        # Handle CSV source type
        if source_type == DatabaseSourceType.CSV:
            if not os.path.exists(source):
                raise SQLToolError(f"CSV file '{source}' does not exist")
            if not source.endswith(".csv"):
                raise SQLToolError(f"File '{source}' is not a CSV file")
            if tables and len(tables) > 1:
                raise SQLToolError("CSV source type only supports one table")

            # Create database name from CSV filename or use custom table name
            base_name = os.path.splitext(os.path.basename(source))[0]
            db_path = os.path.join(os.path.dirname(source), f"{base_name}.db")
            table_name = tables[0] if tables else None
            try:
                # Create database from CSV
                schema = create_database_from_csv(source, db_path, table_name)
                database_path = db_path

                # Get table names if not provided
                if not tables:
                    tables = get_table_names_from_schema(schema)

            except Exception as e:
                if os.path.exists(db_path):
                    try:
                        os.remove(db_path)
                    except Exception as cleanup_error:
                        warnings.warn(f"Failed to remove temporary database file '{db_path}': {str(cleanup_error)}")
                raise SQLToolError(f"Failed to create database from CSV: {str(e)}")

        # Handle SQLite source type
        elif source_type == DatabaseSourceType.SQLITE:
            if not os.path.exists(source):
                raise SQLToolError(f"Database '{source}' does not exist")
            if not source.endswith(".db") and not source.endswith(".sqlite"):
                raise SQLToolError(f"Database '{source}' must have .db or .sqlite extension")

            database_path = source

            # Infer schema from database if not provided
            if not schema:
                try:
                    schema = get_table_schema(database_path)
                except Exception as e:
                    raise SQLToolError(f"Failed to get database schema: {str(e)}")

            # Get table names if not provided
            if not tables:
                try:
                    tables = get_table_names_from_schema(schema)
                except Exception as e:
                    raise SQLToolError(f"Failed to get table names: {str(e)}")

        elif source_type == DatabaseSourceType.POSTGRESQL:
            raise SQLToolError("PostgreSQL is not supported yet")

        # Create and return SQLTool
        return SQLTool(
            name=name,
            description=description,
            database=database_path,
            schema=schema,
            tables=tables,
            enable_commit=enable_commit,
        )

    @classmethod
    def list(cls) -> Dict:
        """List all agents available in the platform."""
        from aixplain.factories.agent_factory.utils import build_agent

        url = urljoin(config.BACKEND_URL, "sdk/agents")
        headers = {"x-api-key": config.TEAM_API_KEY, "Content-Type": "application/json"}

        resp = {}
        payload = {}
        logging.info(f"Start service for GET List Agents - {url} - {headers} - {json.dumps(payload)}")
        try:
            r = _request_with_retry("get", url, headers=headers)
            resp = r.json()
        except Exception:
            raise Exception("Agent Listing Error: Please contact the administrators.")

        if 200 <= r.status_code < 300:
            agents, page_total, total = [], 0, 0
            results = resp
            page_total = len(results)
            total = len(results)
            logging.info(f"Response for GET List Agents - Page Total: {page_total} / Total: {total}")
            for agent in results:
                agents.append(build_agent(agent))
            return {"results": agents, "page_total": page_total, "page_number": 0, "total": total}
        else:
            error_msg = "Agent Listing Error: Please contact the administrators."
            if isinstance(resp, dict) and "message" in resp:
                msg = resp["message"]
                error_msg = f"Agent Listing Error (HTTP {r.status_code}): {msg}"
            logging.exception(error_msg)
            raise Exception(error_msg)

    @classmethod
    def get(cls, agent_id: Text, api_key: Optional[Text] = None) -> Agent:
        """Get agent by id."""
        from aixplain.factories.agent_factory.utils import build_agent

        url = urljoin(config.BACKEND_URL, f"sdk/agents/{agent_id}")

        api_key = api_key if api_key is not None else config.TEAM_API_KEY
        headers = {"x-api-key": api_key, "Content-Type": "application/json"}
        logging.info(f"Start service for GET Agent  - {url} - {headers}")
        r = _request_with_retry("get", url, headers=headers)
        resp = r.json()
        if 200 <= r.status_code < 300:
            return build_agent(resp)
        else:
            msg = "Please contact the administrators."
            if "message" in resp:
                msg = resp["message"]
            error_msg = f"Agent Get Error (HTTP {r.status_code}): {msg}"
            raise Exception(error_msg)