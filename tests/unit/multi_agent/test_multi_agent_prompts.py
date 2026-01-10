"""
Tests for multi-agent prompt builders and configurations.
"""

import pytest

from src.multi_agent.infrastructure.prompts.multi_agent_prompts import (
    PERSONALITY_STYLES,
    PROFESSION_FOCUS,
    Personality,
    Profession,
    build_agent_system_prompt,
    build_debate_context,
    build_round_prompt,
    build_synthesis_prompt,
)


class TestPersonalityEnum:
    """Tests for Personality enum."""

    def test_all_personalities_defined(self):
        """All expected personalities should be defined."""
        expected = [
            "CONSERVATIVE",
            "AGGRESSIVE",
            "ANALYTICAL",
            "PRAGMATIC",
            "INNOVATIVE",
        ]
        actual = [p.name for p in Personality]
        assert set(expected) == set(actual)

    def test_personality_values_are_spanish(self):
        """Personality values should be in Spanish."""
        assert Personality.CONSERVATIVE.value == "Conservador"
        assert Personality.AGGRESSIVE.value == "Agresivo"
        assert Personality.ANALYTICAL.value == "Analítico"
        assert Personality.PRAGMATIC.value == "Pragmático"
        assert Personality.INNOVATIVE.value == "Innovador"

    def test_personality_is_string_enum(self):
        """Personality should be string enum for easy serialization."""
        for p in Personality:
            assert isinstance(p.value, str)


class TestProfessionEnum:
    """Tests for Profession enum."""

    def test_all_professions_defined(self):
        """All expected professions should be defined."""
        expected = [
            "AUDITOR",
            "TAX_PLANNER",
            "ACCOUNTANT",
            "FINANCIAL_ADVISOR",
            "FISCAL_LAWYER",
            "BUSINESS_CONSULTANT",
        ]
        actual = [p.name for p in Profession]
        assert set(expected) == set(actual)

    def test_profession_values_are_spanish(self):
        """Profession values should be in Spanish."""
        assert Profession.AUDITOR.value == "Auditor Fiscal"
        assert Profession.TAX_PLANNER.value == "Planificador Fiscal"
        assert Profession.ACCOUNTANT.value == "Contador Público"

    def test_profession_is_string_enum(self):
        """Profession should be string enum for easy serialization."""
        for p in Profession:
            assert isinstance(p.value, str)


class TestPersonalityStyles:
    """Tests for personality style configurations."""

    def test_all_personalities_have_styles(self):
        """All personalities should have style configurations."""
        for personality in Personality:
            assert personality in PERSONALITY_STYLES

    def test_style_has_required_keys(self):
        """Each style config should have required keys."""
        required_keys = ["tone", "approach", "style", "phrases"]
        for personality, config in PERSONALITY_STYLES.items():
            for key in required_keys:
                assert key in config, f"{personality} missing {key}"

    def test_phrases_are_non_empty_list(self):
        """Each personality should have at least one phrase."""
        for personality, config in PERSONALITY_STYLES.items():
            assert len(config["phrases"]) > 0
            assert all(isinstance(p, str) for p in config["phrases"])

    def test_conservative_is_cautious(self):
        """Conservative personality should emphasize caution."""
        config = PERSONALITY_STYLES[Personality.CONSERVATIVE]
        assert "cautel" in config["tone"].lower() or "precav" in config["tone"].lower()

    def test_aggressive_seeks_opportunities(self):
        """Aggressive personality should seek opportunities."""
        config = PERSONALITY_STYLES[Personality.AGGRESSIVE]
        assert (
            "oportunidad" in config["approach"].lower()
            or "audaz" in config["tone"].lower()
        )

    def test_analytical_uses_data(self):
        """Analytical personality should focus on data."""
        config = PERSONALITY_STYLES[Personality.ANALYTICAL]
        assert (
            "dato" in config["approach"].lower()
            or "análisis" in config["style"].lower()
        )


class TestProfessionFocus:
    """Tests for profession focus configurations."""

    def test_all_professions_have_focus(self):
        """All professions should have focus configurations."""
        for profession in Profession:
            assert profession in PROFESSION_FOCUS

    def test_focus_has_required_keys(self):
        """Each focus config should have required keys."""
        required_keys = ["expertise", "focus_areas", "priorities"]
        for profession, config in PROFESSION_FOCUS.items():
            for key in required_keys:
                assert key in config, f"{profession} missing {key}"

    def test_focus_areas_are_non_empty(self):
        """Each profession should have focus areas."""
        for profession, config in PROFESSION_FOCUS.items():
            assert len(config["focus_areas"]) > 0

    def test_priorities_are_non_empty(self):
        """Each profession should have priorities."""
        for profession, config in PROFESSION_FOCUS.items():
            assert len(config["priorities"]) > 0

    def test_auditor_focuses_on_compliance(self):
        """Auditor should focus on compliance."""
        config = PROFESSION_FOCUS[Profession.AUDITOR]
        assert "cumplimiento" in config["expertise"].lower()

    def test_tax_planner_focuses_on_optimization(self):
        """Tax planner should focus on optimization."""
        config = PROFESSION_FOCUS[Profession.TAX_PLANNER]
        assert "optimización" in config["expertise"].lower()


class TestBuildAgentSystemPrompt:
    """Tests for build_agent_system_prompt function."""

    def test_prompt_contains_agent_name(self):
        """System prompt should include agent name."""
        prompt = build_agent_system_prompt(
            personality=Personality.CONSERVATIVE,
            profession=Profession.AUDITOR,
            agent_name="María González",
        )
        assert "María González" in prompt

    def test_prompt_contains_profession(self):
        """System prompt should include profession."""
        prompt = build_agent_system_prompt(
            personality=Personality.CONSERVATIVE,
            profession=Profession.AUDITOR,
            agent_name="Test Agent",
        )
        assert "Auditor Fiscal" in prompt

    def test_prompt_contains_personality(self):
        """System prompt should include personality."""
        prompt = build_agent_system_prompt(
            personality=Personality.AGGRESSIVE,
            profession=Profession.TAX_PLANNER,
            agent_name="Test Agent",
        )
        assert "Agresivo" in prompt

    def test_prompt_contains_expertise(self):
        """System prompt should include professional expertise."""
        prompt = build_agent_system_prompt(
            personality=Personality.ANALYTICAL,
            profession=Profession.ACCOUNTANT,
            agent_name="Test Agent",
        )
        assert "contable" in prompt.lower() or "cálculo" in prompt.lower()

    def test_prompt_contains_character_limit_instruction(self):
        """System prompt should mention character limits."""
        prompt = build_agent_system_prompt(
            personality=Personality.PRAGMATIC,
            profession=Profession.FINANCIAL_ADVISOR,
            agent_name="Test Agent",
        )
        assert "150-250" in prompt or "caracteres" in prompt.lower()

    def test_prompt_contains_off_topic_instruction(self):
        """System prompt should include off-topic handling."""
        prompt = build_agent_system_prompt(
            personality=Personality.INNOVATIVE,
            profession=Profession.FISCAL_LAWYER,
            agent_name="Test Agent",
        )
        assert "Fuera del tema" in prompt or "fiscal" in prompt.lower()

    def test_prompt_is_not_empty(self):
        """System prompt should never be empty."""
        prompt = build_agent_system_prompt(
            personality=Personality.CONSERVATIVE,
            profession=Profession.AUDITOR,
            agent_name="Test",
        )
        assert len(prompt) > 100

    def test_all_personality_profession_combinations(self):
        """All combinations should produce valid prompts."""
        for personality in Personality:
            for profession in Profession:
                prompt = build_agent_system_prompt(
                    personality=personality,
                    profession=profession,
                    agent_name="Test Agent",
                )
                assert len(prompt) > 100
                assert personality.value in prompt
                assert profession.value in prompt


class TestBuildDebateContext:
    """Tests for build_debate_context function."""

    @pytest.fixture
    def sample_calculation_dict(self) -> dict:
        """Sample calculation as dictionary."""
        return {
            "gross_annual_income": 300000.0,
            "determined_tax": 40000.0,
            "withheld_tax": 45000.0,
            "balance_in_favor": 5000.0,
        }

    @pytest.fixture
    def sample_user_data(self) -> dict:
        """Sample user data."""
        return {
            "deduction_data": {
                "general_deductions": 20000.0,
                "ppr_deductions": 15000.0,
                "education_deductions": 5000.0,
            }
        }

    def test_context_contains_fiscal_year(
        self, sample_calculation_dict, sample_user_data
    ):
        """Context should include fiscal year."""
        context = build_debate_context(
            calculation_result=sample_calculation_dict,
            user_data=sample_user_data,
            fiscal_year=2024,
            uma_annual=39606.36,
            effective_deduction_limit=59409.54,
        )
        assert "2024" in context

    def test_context_contains_income(self, sample_calculation_dict, sample_user_data):
        """Context should include income figures."""
        context = build_debate_context(
            calculation_result=sample_calculation_dict,
            user_data=sample_user_data,
            fiscal_year=2024,
            uma_annual=39606.36,
            effective_deduction_limit=59409.54,
        )
        assert "300,000" in context or "300000" in context

    def test_context_contains_balance_status_favor(
        self, sample_calculation_dict, sample_user_data
    ):
        """Context should show 'saldo a favor' for positive balance."""
        context = build_debate_context(
            calculation_result=sample_calculation_dict,
            user_data=sample_user_data,
            fiscal_year=2024,
            uma_annual=39606.36,
            effective_deduction_limit=59409.54,
        )
        assert "saldo a favor" in context.lower()

    def test_context_contains_balance_status_pagar(self, sample_user_data):
        """Context should show 'a pagar' for negative balance."""
        calculation = {
            "gross_annual_income": 300000.0,
            "determined_tax": 50000.0,
            "withheld_tax": 40000.0,
            "balance_in_favor": 0.0,
        }
        context = build_debate_context(
            calculation_result=calculation,
            user_data=sample_user_data,
            fiscal_year=2024,
            uma_annual=39606.36,
            effective_deduction_limit=59409.54,
        )
        assert "a pagar" in context.lower()

    def test_context_contains_deduction_totals(
        self, sample_calculation_dict, sample_user_data
    ):
        """Context should include total deductions."""
        context = build_debate_context(
            calculation_result=sample_calculation_dict,
            user_data=sample_user_data,
            fiscal_year=2024,
            uma_annual=39606.36,
            effective_deduction_limit=59409.54,
        )
        # Total deductions = 20000 + 15000 + 5000 = 40000
        assert "40,000" in context or "40000" in context

    def test_context_contains_remaining_space(
        self, sample_calculation_dict, sample_user_data
    ):
        """Context should include remaining deduction space."""
        context = build_debate_context(
            calculation_result=sample_calculation_dict,
            user_data=sample_user_data,
            fiscal_year=2024,
            uma_annual=39606.36,
            effective_deduction_limit=59409.54,
        )
        # Remaining = 59409.54 - 40000 = 19409.54
        assert "Espacio disponible" in context

    def test_context_handles_object_calculation(self, sample_user_data):
        """Context should work with object-style calculation result."""

        class MockCalculation:
            gross_annual_income = 200000.0
            determined_tax = 30000.0
            withheld_tax = 32000.0
            balance_in_favor = 2000.0

        context = build_debate_context(
            calculation_result=MockCalculation(),
            user_data=sample_user_data,
            fiscal_year=2025,
            uma_annual=39606.36,
            effective_deduction_limit=50000.0,
        )
        assert "200,000" in context or "200000" in context

    def test_context_handles_empty_deductions(self, sample_calculation_dict):
        """Context should handle empty deduction data."""
        context = build_debate_context(
            calculation_result=sample_calculation_dict,
            user_data={},
            fiscal_year=2024,
            uma_annual=39606.36,
            effective_deduction_limit=59409.54,
        )
        assert "Deducciones actuales: $0" in context


class TestBuildRoundPrompt:
    """Tests for build_round_prompt function."""

    @pytest.fixture
    def sample_context(self) -> str:
        return "CONTEXTO FISCAL 2024:\nIngresos: $300,000\nISR: $40,000"

    def test_initial_round_prompt(self, sample_context):
        """Initial round should have proposal prompt."""
        prompt = build_round_prompt(
            round_number=1,
            round_type="initial",
            context=sample_context,
        )
        assert "RONDA 1" in prompt
        assert "PROPUESTA" in prompt.upper() or "estrategia" in prompt.lower()
        assert sample_context in prompt

    def test_response_round_includes_previous_arguments(self, sample_context):
        """Response round should include previous arguments."""
        previous_args = [
            {"agent": "María", "content": "Mi propuesta es..."},
            {"agent": "Carlos", "content": "Sugiero que..."},
        ]
        prompt = build_round_prompt(
            round_number=2,
            round_type="response",
            context=sample_context,
            previous_arguments=previous_args,
        )
        assert "María" in prompt
        assert "Carlos" in prompt
        assert "Mi propuesta es" in prompt

    def test_consensus_round_prompt(self, sample_context):
        """Consensus round should ask for prioritization."""
        prompt = build_round_prompt(
            round_number=3,
            round_type="consensus",
            context=sample_context,
        )
        assert "CONSENSO" in prompt.upper() or "PRIORIZACIÓN" in prompt.upper()
        assert "voto" in prompt.lower() or "prioriza" in prompt.lower()

    def test_prompt_contains_character_limit(self, sample_context):
        """All prompts should mention character limits."""
        for round_type in ["initial", "response", "consensus"]:
            prompt = build_round_prompt(
                round_number=1,
                round_type=round_type,
                context=sample_context,
            )
            assert "150-250" in prompt or "caracteres" in prompt.lower()

    def test_unknown_round_type_fallback(self, sample_context):
        """Unknown round type should produce fallback prompt."""
        prompt = build_round_prompt(
            round_number=4,
            round_type="unknown",
            context=sample_context,
        )
        assert "RONDA 4" in prompt
        assert len(prompt) > 10


class TestBuildSynthesisPrompt:
    """Tests for build_synthesis_prompt function."""

    @pytest.fixture
    def sample_arguments(self) -> list:
        return [
            {"agent": "María", "content": "Propuesta inicial", "round": 1},
            {"agent": "Carlos", "content": "Otra propuesta", "round": 1},
            {"agent": "María", "content": "Respuesta", "round": 2},
            {"agent": "Carlos", "content": "Debate", "round": 2},
            {"agent": "María", "content": "Consenso", "round": 3},
        ]

    @pytest.fixture
    def sample_context(self) -> str:
        return "CONTEXTO FISCAL 2024:\nIngresos: $300,000"

    def test_synthesis_includes_all_agents(self, sample_arguments, sample_context):
        """Synthesis should include all agent names."""
        prompt = build_synthesis_prompt(
            all_arguments=sample_arguments,
            context=sample_context,
        )
        assert "María" in prompt
        assert "Carlos" in prompt

    def test_synthesis_includes_context(self, sample_arguments, sample_context):
        """Synthesis should include fiscal context."""
        prompt = build_synthesis_prompt(
            all_arguments=sample_arguments,
            context=sample_context,
        )
        assert "300,000" in prompt

    def test_synthesis_requests_action_plan(self, sample_arguments, sample_context):
        """Synthesis should request action plan."""
        prompt = build_synthesis_prompt(
            all_arguments=sample_arguments,
            context=sample_context,
        )
        assert "plan de acción" in prompt.lower() or "pasos" in prompt.lower()

    def test_synthesis_requests_markdown(self, sample_arguments, sample_context):
        """Synthesis should request Markdown format."""
        prompt = build_synthesis_prompt(
            all_arguments=sample_arguments,
            context=sample_context,
        )
        assert "Markdown" in prompt or "markdown" in prompt.lower()

    def test_synthesis_groups_by_round(self, sample_arguments, sample_context):
        """Synthesis should group arguments by round."""
        prompt = build_synthesis_prompt(
            all_arguments=sample_arguments,
            context=sample_context,
        )
        assert "Ronda 1" in prompt
        assert "Ronda 2" in prompt
        assert "Ronda 3" in prompt

    def test_synthesis_has_word_limit(self, sample_arguments, sample_context):
        """Synthesis should mention word limit."""
        prompt = build_synthesis_prompt(
            all_arguments=sample_arguments,
            context=sample_context,
        )
        assert "600" in prompt or "palabras" in prompt.lower()

    def test_synthesis_empty_arguments(self, sample_context):
        """Synthesis should handle empty arguments list."""
        prompt = build_synthesis_prompt(
            all_arguments=[],
            context=sample_context,
        )
        assert len(prompt) > 100
        assert sample_context in prompt
