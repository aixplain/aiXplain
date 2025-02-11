from typing import Dict, Any, Text, Optional


class MonitoringTools:
    def __init__(self, agentops_api_key: Optional[Text] = None, config: Optional[Dict] = None):
        """Initialize MonitoringTools with either direct parameters or a config dictionary.

        Args:
            agentops_api_key (Optional[Text]): Direct API key parameter
            config (Optional[Dict]): Configuration dictionary that may contain platform settings
        """
        if config is not None:
            agentops_config = config.get("agentops", {})
            self.agentops_api_key = agentops_config.get("api_key", agentops_api_key)
        else:
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
