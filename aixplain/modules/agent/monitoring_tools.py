from typing import Dict, Any, Text, Optional, List


class MonitoringTools:
    def __init__(
        self, agentops_api_key: Optional[Text] = None, config: Optional[Dict] = None, tools: Optional[List[Dict]] = None
    ):
        """Initialize MonitoringTools with either direct parameters, a config dictionary, or a list of tools.

        Args:
            agentops_api_key (Optional[Text]): Direct API key parameter
            config (Optional[Dict]): Configuration dictionary that may contain platform settings
            tools (Optional[List[Dict]]): List of monitoring tool configurations in the format:
                [{"type": "monitoring", "description": "agentops", "parameters": [{"api_key": "..."}]}]
        """
        self.agentops_api_key = None

        # Process tools list if provided
        if tools:
            for tool in tools:
                if tool.get("type") == "monitoring" and tool.get("description", "").lower() == "agentops":
                    parameters = tool.get("parameters", [])
                    if parameters and isinstance(parameters, list):
                        parameter_name = parameters[0].get("name")
                        parameter_value = parameters[0].get("value")
                        if parameter_name == "api_key":
                            self.agentops_api_key = parameter_value

        # Process config if provided and agentops_api_key not set from tools
        if self.agentops_api_key is None and config is not None:
            agentops_config = config.get("agentops", {})
            self.agentops_api_key = agentops_config.get("api_key", agentops_api_key)

        # Use direct parameter if still not set
        if self.agentops_api_key is None:
            self.agentops_api_key = agentops_api_key

    def to_dict(self) -> Dict[str, Dict[str, Any]]:
        """Convert parameters back to dictionary format.

        Returns:
            Dict[str, Dict[str, Any]]: Dictionary representation of parameters
        """
        platforms = {}

        if self.agentops_api_key:
            platforms["agentops"] = {"api_key": self.agentops_api_key}

        return platforms

    def to_list(self) -> List[str]:
        """Convert parameters back to list format.

        Returns:
            List[str]: List representation of parameters
        """
        result = []
        if self.agentops_api_key:
            result.append(
                {
                    "type": "monitoring",
                    "description": "agentops",
                    "parameters": [{"name": "api_key", "value": self.agentops_api_key}],
                }
            )
        return result

    def __str__(self) -> str:
        """Create a pretty string representation of the parameters.

        Returns:
            str: Formatted string showing all parameters
        """
        if not any([self.agentops_api_key]):
            return "No monitoring tools configured"

        output = ["Parameters:"]
        if self.agentops_api_key:
            output.append(f"  - AgentOps API Key: {'*' * 8}{self.agentops_api_key[-4:]}")

        return "\n".join(output)
