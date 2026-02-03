"""
Unit tests for Agent evolve functionality with llm parameter
"""

import pytest
from unittest.mock import Mock, patch
from aixplain.modules.agent import Agent
from aixplain.modules.model.llm_model import LLM
from aixplain.modules.agent.evolve_param import EvolveParam
from aixplain.enums import EvolveType, Function, Supplier, ResponseStatus
from aixplain.modules.agent.agent_response import AgentResponse
from aixplain.modules.agent.agent_response_data import AgentResponseData


class TestAgentEvolve:
    """Test class for Agent evolve functionality"""

    @pytest.fixture
    def mock_agent(self):
        """Create a mock Agent for testing"""
        agent = Mock(spec=Agent)
        agent.id = "test_agent_id"
        agent.name = "Test Agent"
        agent.api_key = "test_api_key"
        return agent

    @pytest.fixture
    def mock_llm(self):
        """Create a mock LLM for testing"""
        llm = Mock(spec=LLM)
        llm.id = "test_llm_id"
        llm.name = "Test LLM"
        llm.description = "Test LLM Description"
        llm.supplier = Supplier.OPENAI
        llm.version = "1.0.0"
        llm.function = Function.TEXT_GENERATION
        llm.temperature = 0.7

        # Mock get_parameters
        mock_params = Mock()
        mock_params.to_list.return_value = [{"name": "temperature", "type": "float"}]
        llm.get_parameters.return_value = mock_params

        return llm

    def test_evolve_async_with_llm_string(self, mock_agent):
        """Test evolve_async with llm as string ID"""
        from aixplain.modules.agent import Agent

        # Create a real Agent instance but mock its methods
        agent = Agent(
            id="test_agent_id",
            name="Test Agent",
            description="Test Description",
            instructions="Test Instructions",
            tools=[],
            llm_id="6646261c6eb563165658bbb1",
        )

        # Mock the run_async method
        mock_response = AgentResponse(
            status=ResponseStatus.IN_PROGRESS,
            url="http://test-poll-url.com",
            data=AgentResponseData(input="test input"),
            run_time=0.0,
            used_credits=0.0,
        )

        with patch.object(agent, "run_async", return_value=mock_response) as mock_run_async:
            result = agent.evolve_async(llm="custom_llm_id_123")

            # Verify run_async was called with correct evolve parameter
            mock_run_async.assert_called_once()
            call_args = mock_run_async.call_args

            # Check that evolve parameter contains llm
            evolve_param = call_args[1]["evolve"]
            assert isinstance(evolve_param, EvolveParam)
            assert evolve_param.llm == {"id": "custom_llm_id_123"}

            assert result == mock_response

    def test_evolve_async_with_llm_object(self, mock_agent, mock_llm):
        """Test evolve_async with llm as LLM object"""
        from aixplain.modules.agent import Agent

        # Create a real Agent instance but mock its methods
        agent = Agent(
            id="test_agent_id",
            name="Test Agent",
            description="Test Description",
            instructions="Test Instructions",
            tools=[],
            llm_id="6646261c6eb563165658bbb1",
        )

        # Mock the run_async method
        mock_response = AgentResponse(
            status=ResponseStatus.IN_PROGRESS,
            url="http://test-poll-url.com",
            data=AgentResponseData(input="test input"),
            run_time=0.0,
            used_credits=0.0,
        )

        with patch.object(agent, "run_async", return_value=mock_response) as mock_run_async:
            result = agent.evolve_async(llm=mock_llm)

            # Verify run_async was called with correct evolve parameter
            mock_run_async.assert_called_once()
            call_args = mock_run_async.call_args

            # Check that evolve parameter contains llm
            evolve_param = call_args[1]["evolve"]
            assert isinstance(evolve_param, EvolveParam)

            expected_llm_dict = {
                "id": "test_llm_id",
                "name": "Test LLM",
                "description": "Test LLM Description",
                "supplier": "openai",
                "version": "1.0.0",
                "function": "text-generation",
                "parameters": [{"name": "temperature", "type": "float"}],
                "temperature": 0.7,
            }
            assert evolve_param.llm == expected_llm_dict

            assert result == mock_response

    def test_evolve_async_without_llm(self, mock_agent):
        """Test evolve_async without llm parameter"""
        from aixplain.modules.agent import Agent

        # Create a real Agent instance but mock its methods
        agent = Agent(
            id="test_agent_id",
            name="Test Agent",
            description="Test Description",
            instructions="Test Instructions",
            tools=[],
            llm_id="6646261c6eb563165658bbb1",
        )

        # Mock the run_async method
        mock_response = AgentResponse(
            status=ResponseStatus.IN_PROGRESS,
            url="http://test-poll-url.com",
            data=AgentResponseData(input="test input"),
            run_time=0.0,
            used_credits=0.0,
        )

        with patch.object(agent, "run_async", return_value=mock_response) as mock_run_async:
            result = agent.evolve_async()

            # Verify run_async was called with correct evolve parameter
            mock_run_async.assert_called_once()
            call_args = mock_run_async.call_args

            # Check that evolve parameter has llm as None
            evolve_param = call_args[1]["evolve"]
            assert isinstance(evolve_param, EvolveParam)
            assert evolve_param.llm is None

            assert result == mock_response

    def test_evolve_with_custom_parameters(self, mock_agent):
        """Test evolve with custom parameters including llm"""
        from aixplain.modules.agent import Agent

        # Create a real Agent instance but mock its methods
        agent = Agent(
            id="test_agent_id",
            name="Test Agent",
            description="Test Description",
            instructions="Test Instructions",
            tools=[],
            llm_id="6646261c6eb563165658bbb1",
        )

        with (
            patch.object(agent, "evolve_async") as mock_evolve_async,
            patch.object(agent, "sync_poll") as mock_sync_poll,
        ):
            # Mock evolve_async response
            mock_evolve_async.return_value = {"status": ResponseStatus.IN_PROGRESS, "url": "http://test-poll-url.com"}

            # Mock sync_poll response
            mock_result = Mock()
            mock_result.data = {"current_code": "test code", "evolved_agent": "evolved_agent_data"}
            mock_sync_poll.return_value = mock_result

            result = agent.evolve(
                evolve_type=EvolveType.TEAM_TUNING,
                max_successful_generations=5,
                max_failed_generation_retries=3,
                max_iterations=40,
                max_non_improving_generations=3,
                llm="custom_llm_id",
            )

            # Verify evolve_async was called with correct parameters
            mock_evolve_async.assert_called_once_with(
                evolve_type=EvolveType.TEAM_TUNING,
                max_successful_generations=5,
                max_failed_generation_retries=3,
                max_iterations=40,
                max_non_improving_generations=3,
                llm="custom_llm_id",
            )

            # Verify sync_poll was called
            mock_sync_poll.assert_called_once_with("http://test-poll-url.com", name="evolve_process", timeout=600)

            assert result is not None
