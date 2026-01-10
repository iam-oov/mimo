"""
Tests for MultiAgentDebateService.
"""

import random
from unittest.mock import MagicMock, patch

import pytest

from src.multi_agent.application.multi_agent_debate_service import (
    AgentConfig,
    DebateRound,
    MultiAgentDebateService,
)
from src.multi_agent.infrastructure.prompts.multi_agent_prompts import (
    Personality,
    Profession,
)


class TestAgentConfig:
    """Tests for AgentConfig dataclass."""

    def test_agent_config_creation(self):
        """AgentConfig should be created with all fields."""
        config = AgentConfig(
            agent_id="agent_1",
            name="María González",
            personality=Personality.CONSERVATIVE,
            profession=Profession.AUDITOR,
        )

        assert config.agent_id == "agent_1"
        assert config.name == "María González"
        assert config.personality == Personality.CONSERVATIVE
        assert config.profession == Profession.AUDITOR

    def test_agent_config_with_all_personalities(self):
        """AgentConfig should work with all personalities."""
        for personality in Personality:
            config = AgentConfig(
                agent_id="test",
                name="Test",
                personality=personality,
                profession=Profession.ACCOUNTANT,
            )
            assert config.personality == personality

    def test_agent_config_with_all_professions(self):
        """AgentConfig should work with all professions."""
        for profession in Profession:
            config = AgentConfig(
                agent_id="test",
                name="Test",
                personality=Personality.ANALYTICAL,
                profession=profession,
            )
            assert config.profession == profession


class TestDebateRound:
    """Tests for DebateRound dataclass."""

    def test_debate_round_creation(self):
        """DebateRound should be created with all fields."""
        round_data = DebateRound(
            round_number=1,
            round_type="initial",
            arguments=[{"agent": "María", "content": "My proposal"}],
        )

        assert round_data.round_number == 1
        assert round_data.round_type == "initial"
        assert len(round_data.arguments) == 1

    def test_debate_round_types(self):
        """DebateRound should support all round types."""
        for round_type in ["initial", "response", "consensus"]:
            round_data = DebateRound(
                round_number=1,
                round_type=round_type,
                arguments=[],
            )
            assert round_data.round_type == round_type


class TestMultiAgentDebateServiceInitialization:
    """Tests for service initialization."""

    def test_service_initialization(self):
        """Service should initialize with default configuration."""
        service = MultiAgentDebateService()

        assert len(service.personalities) == len(Personality)
        assert len(service.professions) == len(Profession)
        assert len(service.names) >= 3  # At least 3 names for agents

    def test_service_has_mexican_names(self):
        """Service should use Mexican names."""
        service = MultiAgentDebateService()

        # Check for common Mexican name patterns
        names_lower = [n.lower() for n in service.names]
        assert any(
            "gonzález" in n or "martínez" in n or "torres" in n for n in names_lower
        )


class TestCreateAgents:
    """Tests for _create_agents method."""

    def test_creates_correct_number_of_agents(self):
        """Should create requested number of agents."""
        service = MultiAgentDebateService()

        for num in [1, 2, 3]:
            agents = service._create_agents(num)
            assert len(agents) == num

    def test_agents_have_unique_ids(self):
        """All agents should have unique IDs."""
        service = MultiAgentDebateService()
        agents = service._create_agents(3)

        ids = [a.agent_id for a in agents]
        assert len(ids) == len(set(ids))

    def test_agents_have_unique_names(self):
        """All agents should have unique names."""
        service = MultiAgentDebateService()
        agents = service._create_agents(3)

        names = [a.name for a in agents]
        assert len(names) == len(set(names))

    def test_agents_have_unique_personalities(self):
        """Agents should have different personalities."""
        service = MultiAgentDebateService()
        agents = service._create_agents(3)

        personalities = [a.personality for a in agents]
        assert len(personalities) == len(set(personalities))

    def test_agents_have_unique_professions(self):
        """Agents should have different professions."""
        service = MultiAgentDebateService()
        agents = service._create_agents(3)

        professions = [a.profession for a in agents]
        assert len(professions) == len(set(professions))

    def test_agents_are_randomized(self):
        """Agents should be randomized between calls."""
        service = MultiAgentDebateService()

        # Run multiple times and check for variation
        all_names = []
        for _ in range(5):
            agents = service._create_agents(3)
            all_names.append(tuple(a.name for a in agents))

        # At least some combinations should be different
        # (with 6 names and 3 agents, probability of all same is very low)
        unique_combinations = len(set(all_names))
        assert unique_combinations >= 2  # Should have some variation

    def test_agent_id_format(self):
        """Agent IDs should follow expected format."""
        service = MultiAgentDebateService()
        agents = service._create_agents(3)

        for i, agent in enumerate(agents):
            assert agent.agent_id == f"agent_{i + 1}"


class TestRunAnalysisStream:
    """Tests for run_analysis_stream method."""

    @pytest.fixture
    def sample_calculation(self) -> dict:
        return {
            "gross_annual_income": 300000.0,
            "determined_tax": 40000.0,
            "withheld_tax": 45000.0,
            "balance_in_favor": 5000.0,
        }

    @pytest.fixture
    def sample_user_data(self) -> dict:
        return {
            "deduction_data": {
                "general_deductions": 20000.0,
                "ppr_deductions": 15000.0,
                "education_deductions": 5000.0,
            }
        }

    @patch(
        "src.multi_agent.application.multi_agent_debate_service.create_agent_adapter"
    )
    def test_stream_yields_agent_intro(
        self, mock_adapter, sample_calculation, sample_user_data
    ):
        """Stream should yield agent introduction event."""
        # Mock adapter that yields chunks
        mock_instance = MagicMock()
        mock_instance.generate_stream.return_value = iter(["Test ", "response"])
        mock_adapter.return_value = mock_instance

        service = MultiAgentDebateService()
        events = list(
            service.run_analysis_stream(sample_calculation, sample_user_data, 2024)
        )

        intro_events = [e for e in events if e.get("type") == "agent_intro"]
        assert len(intro_events) == 1
        assert "agents" in intro_events[0]
        assert len(intro_events[0]["agents"]) == 3

    @patch(
        "src.multi_agent.application.multi_agent_debate_service.create_agent_adapter"
    )
    def test_stream_yields_round_starts(
        self, mock_adapter, sample_calculation, sample_user_data
    ):
        """Stream should yield round start events for all 3 rounds."""
        mock_instance = MagicMock()
        mock_instance.generate_stream.return_value = iter(["Test"])
        mock_adapter.return_value = mock_instance

        service = MultiAgentDebateService()
        events = list(
            service.run_analysis_stream(sample_calculation, sample_user_data, 2024)
        )

        round_starts = [e for e in events if e.get("type") == "round_start"]
        assert len(round_starts) == 3

        round_numbers = [e["round_number"] for e in round_starts]
        assert round_numbers == [1, 2, 3]

    @patch(
        "src.multi_agent.application.multi_agent_debate_service.create_agent_adapter"
    )
    def test_stream_yields_agent_turns(
        self, mock_adapter, sample_calculation, sample_user_data
    ):
        """Stream should yield agent turn events."""
        mock_instance = MagicMock()
        mock_instance.generate_stream.return_value = iter(["Test"])
        mock_adapter.return_value = mock_instance

        service = MultiAgentDebateService()
        events = list(
            service.run_analysis_stream(sample_calculation, sample_user_data, 2024)
        )

        agent_turns = [e for e in events if e.get("type") == "agent_turn"]
        # 3 agents × 3 rounds = 9 turns
        assert len(agent_turns) == 9

    @patch(
        "src.multi_agent.application.multi_agent_debate_service.create_agent_adapter"
    )
    def test_stream_yields_chunks(
        self, mock_adapter, sample_calculation, sample_user_data
    ):
        """Stream should yield content chunks."""
        mock_instance = MagicMock()
        mock_instance.generate_stream.return_value = iter(["Chunk1", "Chunk2"])
        mock_adapter.return_value = mock_instance

        service = MultiAgentDebateService()
        events = list(
            service.run_analysis_stream(sample_calculation, sample_user_data, 2024)
        )

        chunk_events = [e for e in events if e.get("type") == "agent_chunk"]
        assert len(chunk_events) > 0

    @patch(
        "src.multi_agent.application.multi_agent_debate_service.create_agent_adapter"
    )
    def test_stream_yields_agent_complete(
        self, mock_adapter, sample_calculation, sample_user_data
    ):
        """Stream should yield agent complete events after each turn."""
        mock_instance = MagicMock()
        mock_instance.generate_stream.return_value = iter(["Test"])
        mock_adapter.return_value = mock_instance

        service = MultiAgentDebateService()
        events = list(
            service.run_analysis_stream(sample_calculation, sample_user_data, 2024)
        )

        complete_events = [e for e in events if e.get("type") == "agent_complete"]
        # Should match number of agent turns
        assert len(complete_events) == 9

    @patch(
        "src.multi_agent.application.multi_agent_debate_service.create_agent_adapter"
    )
    def test_stream_handles_adapter_error(
        self, mock_adapter, sample_calculation, sample_user_data
    ):
        """Stream should handle adapter errors gracefully."""
        mock_instance = MagicMock()
        mock_instance.generate_stream.side_effect = Exception("API Error")
        mock_adapter.return_value = mock_instance

        service = MultiAgentDebateService()
        # Should not raise, but continue with error message
        events = list(
            service.run_analysis_stream(sample_calculation, sample_user_data, 2024)
        )

        # Should still have events (intro, round starts, etc.)
        assert len(events) > 0

    @patch(
        "src.multi_agent.application.multi_agent_debate_service.create_agent_adapter"
    )
    def test_stream_handles_no_adapter(
        self, mock_adapter, sample_calculation, sample_user_data
    ):
        """Stream should handle missing adapter gracefully."""
        mock_adapter.return_value = None

        service = MultiAgentDebateService()
        events = list(
            service.run_analysis_stream(sample_calculation, sample_user_data, 2024)
        )

        # Should still yield intro and round starts
        intro_events = [e for e in events if e.get("type") == "agent_intro"]
        assert len(intro_events) == 1

    @patch(
        "src.multi_agent.application.multi_agent_debate_service.create_agent_adapter"
    )
    def test_agent_intro_contains_expertise(
        self, mock_adapter, sample_calculation, sample_user_data
    ):
        """Agent intro should include expertise information."""
        mock_instance = MagicMock()
        mock_instance.generate_stream.return_value = iter(["Test"])
        mock_adapter.return_value = mock_instance

        service = MultiAgentDebateService()
        events = list(
            service.run_analysis_stream(sample_calculation, sample_user_data, 2024)
        )

        intro = [e for e in events if e.get("type") == "agent_intro"][0]
        for agent in intro["agents"]:
            assert "expertise" in agent
            assert len(agent["expertise"]) > 0

    @patch(
        "src.multi_agent.application.multi_agent_debate_service.create_agent_adapter"
    )
    def test_stream_uses_correct_fiscal_year(
        self, mock_adapter, sample_calculation, sample_user_data
    ):
        """Stream should use provided fiscal year for calculations."""
        mock_instance = MagicMock()
        mock_instance.generate_stream.return_value = iter(["Test"])
        mock_adapter.return_value = mock_instance

        service = MultiAgentDebateService()

        # Test with different fiscal years
        for year in [2024, 2025, 2026]:
            events = list(
                service.run_analysis_stream(sample_calculation, sample_user_data, year)
            )
            assert len(events) > 0


class TestMultiAgentProviderInterface:
    """Tests for MultiAgentProvider interface."""

    def test_interface_is_abstract(self):
        """MultiAgentProvider should be abstract."""
        from src.multi_agent.domain.ports.multi_agent_provider import MultiAgentProvider

        with pytest.raises(TypeError):
            MultiAgentProvider()

    def test_interface_requires_generate_stream(self):
        """Interface should require generate_stream method."""
        from src.multi_agent.domain.ports.multi_agent_provider import MultiAgentProvider

        class IncompleteProvider(MultiAgentProvider):
            def is_available(self) -> bool:
                return True

            def get_model_name(self) -> str:
                return "test"

        with pytest.raises(TypeError, match="generate_stream"):
            IncompleteProvider()

    def test_interface_requires_is_available(self):
        """Interface should require is_available method."""
        from src.multi_agent.domain.ports.multi_agent_provider import MultiAgentProvider
        from collections.abc import Generator

        class IncompleteProvider(MultiAgentProvider):
            def generate_stream(self, prompt: str) -> Generator[str, None, None]:
                yield "test"

            def get_model_name(self) -> str:
                return "test"

        with pytest.raises(TypeError, match="is_available"):
            IncompleteProvider()

    def test_interface_requires_get_model_name(self):
        """Interface should require get_model_name method."""
        from src.multi_agent.domain.ports.multi_agent_provider import MultiAgentProvider
        from collections.abc import Generator

        class IncompleteProvider(MultiAgentProvider):
            def generate_stream(self, prompt: str) -> Generator[str, None, None]:
                yield "test"

            def is_available(self) -> bool:
                return True

        with pytest.raises(TypeError, match="get_model_name"):
            IncompleteProvider()
