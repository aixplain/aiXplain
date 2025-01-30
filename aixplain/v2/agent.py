from typing_extensions import (
    Unpack,
    List,
    Union,
    TYPE_CHECKING,
    Callable,
    NotRequired,
)

from .resource import (
    BaseResource,
    ListResourceMixin,
    GetResourceMixin,
    BareListParams,
    BareGetParams,
    BaseCreateParams,
    Page,
)

if TYPE_CHECKING:
    from aixplain.modules.agent.tool import Tool
    from aixplain.modules.agent.utils import Supplier
    from aixplain.modules.model import Model
    from aixplain.modules.pipeline import Pipeline
    from aixplain.modules.agent.tool.pipeline_tool import PipelineTool
    from aixplain.modules.agent.tool.python_interpreter_tool import (
        PythonInterpreterTool,
    )
    from aixplain.modules.agent.tool.custom_python_code_tool import CustomPythonCodeTool

from .enums import Function


class AgentCreateParams(BaseCreateParams):
    name: str
    description: str
    llm_id: NotRequired[str]
    tools: NotRequired[List["Tool"]]
    api_key: NotRequired[str]
    supplier: NotRequired[Union[dict, str, "Supplier", int]]
    version: NotRequired[str]


class Agent(
    BaseResource,
    ListResourceMixin[BareListParams, "Agent"],
    GetResourceMixin[BareGetParams, "Agent"],
):
    """Resource for agents.

    Attributes:
        RESOURCE_PATH: str: The resource path.
        PAGINATE_PATH: None: The path for pagination.
        PAGINATE_METHOD: str: The method for pagination.
        PAGINATE_ITEMS_KEY: None: The key for the response.
    """

    RESOURCE_PATH = "sdk/agents"
    PAGINATE_PATH = None
    PAGINATE_METHOD = "get"
    PAGINATE_ITEMS_KEY = None

    LLM_ID = "669a63646eb56306647e1091"
    SUPPLIER = "aiXplain"

    @classmethod
    def list(cls, **kwargs: Unpack[BareListParams]) -> Page["Agent"]:
        from aixplain.factories import AgentFactory

        return AgentFactory.list(**kwargs)

    @classmethod
    def get(cls, id: str, **kwargs: Unpack[BareGetParams]) -> "Agent":
        from aixplain.factories import AgentFactory

        return AgentFactory.get(agent_id=id)

    @classmethod
    def create(cls, *args, **kwargs: Unpack[AgentCreateParams]) -> "Agent":
        from aixplain.factories import AgentFactory
        from aixplain.utils import config

        kwargs.setdefault("llm_id", cls.LLM_ID)
        kwargs.setdefault("api_key", config.TEAM_API_KEY)
        kwargs.setdefault("supplier", cls.SUPPLIER)
        kwargs.setdefault("tools", [])

        return AgentFactory.create(*args, **kwargs)

    @classmethod
    def create_model_tool(
        cls,
        model: Union["Model", str] = None,
        function: Union[Function, str] = None,
        supplier: Union["Supplier", str] = None,
        description: str = "",
    ):
        from aixplain.factories import AgentFactory

        return AgentFactory.create_model_tool(
            model=model, function=function, supplier=supplier, description=description
        )

    @classmethod
    def create_pipeline_tool(
        cls, description: str, pipeline: Union["Pipeline", str]
    ) -> "PipelineTool":
        """Create a new pipeline tool."""
        from aixplain.factories import AgentFactory

        return AgentFactory.create_pipeline_tool(
            description=description, pipeline=pipeline
        )

    @classmethod
    def create_python_interpreter_tool(cls) -> "PythonInterpreterTool":
        """Create a new python interpreter tool."""
        from aixplain.factories import AgentFactory

        return AgentFactory.create_python_interpreter_tool()

    @classmethod
    def create_custom_python_code_tool(
        cls, code: Union[str, Callable], description: str = ""
    ) -> "CustomPythonCodeTool":
        """Create a new custom python code tool."""
        from aixplain.factories import AgentFactory

        return AgentFactory.create_custom_python_code_tool(
            code=code, description=description
        )
