"""Unit tests for simulator.py — heuristic simulation, metrics, ranking."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from simulator import (
    PersonaReaction, ThreadReply, SimulatedMetrics,
    load_personas, heuristic_simulate_persona, simulate_thread_heuristic,
)

pytestmark = pytest.mark.unit


# ─── Load Personas ───


class TestLoadPersonas:
    def test_returns_10_personas(self, postforge_root):
        personas = load_personas()
        assert len(personas) == 10

    def test_all_have_required_keys(self, postforge_root):
        personas = load_personas()
        required = {"name", "display", "role", "scroll_speed", "stops_for",
                    "comment_style", "save_threshold", "skip_threshold"}
        for p in personas:
            assert required.issubset(p.keys()), f"Missing keys in {p.get('name', '?')}"

    def test_persona_types_covered(self, postforge_root):
        personas = load_personas()
        names = [p["name"] for p in personas]
        assert any("founder" in n for n in names)
        assert any("tech_peer" in n for n in names)
        assert any("aspiring" in n for n in names)
        assert any("contrarian" in n for n in names)
        assert any("lurker" in n for n in names)


# ─── Heuristic Simulation ───


def _get_persona(name_part):
    """Get a specific persona by name fragment."""
    personas = load_personas()
    return next(p for p in personas if name_part in p["name"])


class TestHeuristicSimulatePersona:
    @pytest.fixture(autouse=True)
    def _setup_root(self, postforge_root):
        """Ensure postforge_root is available for load_personas."""
        pass

    def test_founder_numbers_indian_context(self):
        persona = _get_persona("founder_pragmatic")
        post = "₹2.3 lakhs per month. That's what a Pune clinic was losing. 47x ROI in India."
        result = heuristic_simulate_persona(persona, post, "text")
        assert isinstance(result, PersonaReaction)
        assert result.action in ("SAVE", "READ")

    def test_founder_generic_skip(self):
        persona = _get_persona("founder_pragmatic")
        post = "Technology is changing the way we work and live every day."
        result = heuristic_simulate_persona(persona, post, "text")
        assert result.action == "SKIP"

    def test_tech_peer_data_bold_comment(self):
        persona = _get_persona("tech_peer_builder")
        post = "Most people think AI deployment takes months. Our data shows 72% complete setup in under 10 hours."
        result = heuristic_simulate_persona(persona, post, "text")
        assert result.action == "COMMENT"
        assert result.comment_text is not None

    def test_contrarian_bold_claim_comment(self):
        persona = _get_persona("contrarian_veteran")
        post = "Nobody is talking about this. Most AI tools are built wrong for Indian SMBs."
        result = heuristic_simulate_persona(persona, post, "text")
        assert result.action == "COMMENT"
        assert result.probability == 85

    def test_aspiring_framework_indian_save(self):
        persona = _get_persona("aspiring_smb_eager")
        post = "Step-by-step framework to automate your business in India with WhatsApp."
        result = heuristic_simulate_persona(persona, post, "text")
        assert result.action == "SAVE"

    def test_lurker_carousel_high_dwell(self):
        persona = _get_persona("lurker_passive")
        post = "A comprehensive guide to AI agents for your business."
        result_text = heuristic_simulate_persona(persona, post, "text")
        result_carousel = heuristic_simulate_persona(persona, post, "carousel")
        assert result_carousel.dwell_seconds >= result_text.dwell_seconds

    def test_returns_valid_dataclass(self):
        persona = _get_persona("tech_peer_critic")
        post = "Here's why AI agents will replace 80% of customer service roles."
        result = heuristic_simulate_persona(persona, post, "text")
        assert isinstance(result, PersonaReaction)
        assert result.persona_name == persona["name"]
        assert result.action in ("SKIP", "SKIM", "READ", "LIKE", "COMMENT", "SAVE", "SHARE")
        assert 0 <= result.probability <= 100
        assert result.dwell_seconds >= 0

    def test_comment_action_has_text(self):
        """Any COMMENT action should have comment_text."""
        persona = _get_persona("contrarian_veteran")
        post = "Most people are wrong about AI in India. The truth nobody shares."
        result = heuristic_simulate_persona(persona, post, "text")
        if result.action == "COMMENT":
            assert result.comment_text is not None
            assert len(result.comment_text) > 0

    def test_skip_action_low_dwell(self):
        persona = _get_persona("founder_pragmatic")
        post = "Just vibes. Nothing specific happening today."
        result = heuristic_simulate_persona(persona, post, "text")
        if result.action == "SKIP":
            assert result.dwell_seconds <= 10

    def test_unknown_persona_type_fallback(self):
        """An unrecognized persona name should get the fallback (SKIM)."""
        persona = {"name": "unknown_type", "display": "Unknown", "role": "test",
                   "scroll_speed": "slow", "stops_for": "anything",
                   "comment_style": "none", "save_threshold": "none",
                   "skip_threshold": "everything"}
        post = "Some AI content about India."
        result = heuristic_simulate_persona(persona, post, "text")
        assert result.action == "SKIM"

    def test_carousel_boost_dwell(self):
        """Carousel format should boost dwell time by 1.5x."""
        persona = _get_persona("aspiring_smb_eager")
        post = "Step-by-step checklist framework for Indian SMBs. ₹4,999 pricing guide."
        result_text = heuristic_simulate_persona(persona, post, "text")
        result_carousel = heuristic_simulate_persona(persona, post, "carousel")
        # Carousel should have higher dwell
        assert result_carousel.dwell_seconds >= result_text.dwell_seconds


# ─── Thread Simulation ───


class TestSimulateThreadHeuristic:
    def test_fewer_than_2_commenters_empty(self):
        reactions = [
            PersonaReaction("tech_peer_builder", "COMMENT", 70, "reason", "Great post!", 30),
            PersonaReaction("lurker_passive", "READ", 60, "reason", None, 40),
        ]
        replies = simulate_thread_heuristic(reactions)
        assert len(replies) == 0

    def test_contrarian_replies_to_non_contrarian(self):
        reactions = [
            PersonaReaction("tech_peer_builder", "COMMENT", 70, "reason", "Great technical insight!", 30),
            PersonaReaction("contrarian_veteran", "COMMENT", 85, "reason", "I disagree with this.", 40),
        ]
        replies = simulate_thread_heuristic(reactions)
        # Contrarian should reply to tech peer
        contrarian_replies = [r for r in replies if "contrarian" in r.author]
        assert len(contrarian_replies) >= 1
        assert contrarian_replies[0].round_num == 1

    def test_tech_peer_responds_round_2(self):
        reactions = [
            PersonaReaction("tech_peer_builder", "COMMENT", 70, "reason", "Here's my experience.", 30),
            PersonaReaction("contrarian_veteran", "COMMENT", 85, "reason", "That's not accurate.", 40),
        ]
        replies = simulate_thread_heuristic(reactions)
        round_2 = [r for r in replies if r.round_num == 2]
        # Tech peer should respond in round 2
        tech_responses = [r for r in round_2 if "tech" in r.author]
        assert len(tech_responses) >= 1

    def test_thread_reply_fields(self):
        reactions = [
            PersonaReaction("tech_peer_builder", "COMMENT", 70, "reason", "Good stuff.", 30),
            PersonaReaction("contrarian_veteran", "COMMENT", 85, "reason", "Disagree.", 40),
        ]
        replies = simulate_thread_heuristic(reactions)
        for reply in replies:
            assert isinstance(reply, ThreadReply)
            assert reply.author
            assert reply.replying_to
            assert reply.text
            assert reply.round_num in (1, 2)

    def test_no_commenters_returns_empty(self):
        reactions = [
            PersonaReaction("lurker_passive", "READ", 60, "reason", None, 40),
            PersonaReaction("founder_pragmatic", "SAVE", 65, "reason", None, 35),
        ]
        assert simulate_thread_heuristic(reactions) == []


# ─── Aggregate Metrics ───


class TestAggregateMetrics:
    def _make_engine(self, postforge_root):
        from simulator import SimulationEngine
        return SimulationEngine(disable_api=True)

    def test_counts_correct(self, postforge_root):
        engine = self._make_engine(postforge_root)
        reactions = [
            PersonaReaction("p1", "COMMENT", 70, "", "text", 30),
            PersonaReaction("p2", "SAVE", 80, "", None, 40),
            PersonaReaction("p3", "SKIP", 60, "", None, 2),
            PersonaReaction("p4", "LIKE", 50, "", None, 10),
            PersonaReaction("p5", "SHARE", 40, "", None, 15),
            PersonaReaction("p6", "READ", 55, "", None, 20),
            PersonaReaction("p7", "SKIM", 45, "", None, 8),
        ]
        threads = []
        metrics = engine._aggregate_metrics(reactions, threads)

        assert metrics.comment_count == 1
        assert metrics.save_count == 1
        assert metrics.share_count == 1
        # LIKE counts: LIKE, COMMENT, SAVE, SHARE = 4
        assert metrics.like_count == 4

    def test_skip_excluded_from_engagement(self, postforge_root):
        engine = self._make_engine(postforge_root)
        reactions = [
            PersonaReaction("p1", "SKIP", 70, "", None, 0),
            PersonaReaction("p2", "SKIP", 70, "", None, 0),
            PersonaReaction("p3", "READ", 70, "", None, 20),
        ]
        metrics = engine._aggregate_metrics(reactions, [])
        # 1 out of 3 engaged
        assert abs(metrics.engagement_rate - (1/3 * 100)) < 0.1

    def test_engagement_rate_formula(self, postforge_root):
        engine = self._make_engine(postforge_root)
        # All engaged (no SKIPs)
        reactions = [
            PersonaReaction("p1", "COMMENT", 70, "", "text", 30),
            PersonaReaction("p2", "SAVE", 80, "", None, 40),
        ]
        metrics = engine._aggregate_metrics(reactions, [])
        assert metrics.engagement_rate == 100.0

    def test_avg_dwell_excludes_zero(self, postforge_root):
        engine = self._make_engine(postforge_root)
        reactions = [
            PersonaReaction("p1", "READ", 70, "", None, 30),
            PersonaReaction("p2", "SKIP", 70, "", None, 0),
            PersonaReaction("p3", "READ", 70, "", None, 50),
        ]
        metrics = engine._aggregate_metrics(reactions, [])
        # Only 30 and 50 count (dwell > 0)
        assert abs(metrics.avg_dwell_seconds - 40.0) < 0.1

    def test_debate_heat_formula(self, postforge_root):
        engine = self._make_engine(postforge_root)
        reactions = [PersonaReaction(f"p{i}", "READ", 50, "", None, 10) for i in range(10)]
        threads = [
            ThreadReply("p1", "p2", "reply1", 1),
            ThreadReply("p3", "p1", "reply2", 1),
        ]
        metrics = engine._aggregate_metrics(reactions, threads)
        # debate_heat = len(threads) * (unique_authors / personas)
        # = 2 * (2 / 10) = 0.4
        assert abs(metrics.debate_heat_score - 0.4) < 0.01

    def test_empty_reactions(self, postforge_root):
        engine = self._make_engine(postforge_root)
        metrics = engine._aggregate_metrics([], [])
        assert metrics.engagement_rate == 0.0
        assert metrics.comment_count == 0


# ─── Rank Variants ───


class TestRankVariants:
    def _make_engine(self, postforge_root):
        from simulator import SimulationEngine, VariantSimulation
        return SimulationEngine(disable_api=True)

    def test_composite_formula(self, postforge_root):
        from simulator import SimulationEngine, VariantSimulation, SimulatedMetrics
        engine = self._make_engine(postforge_root)

        results = {
            "A": VariantSimulation(
                variant_id="A",
                metrics=SimulatedMetrics(save_count=10, comment_count=5, avg_thread_depth=2.0),
            ),
            "B": VariantSimulation(
                variant_id="B",
                metrics=SimulatedMetrics(save_count=5, comment_count=10, avg_thread_depth=1.0),
            ),
        }

        rankings = engine.rank_variants(results)
        # A: 0.40*(10/10) + 0.35*(5/10) + 0.25*(2/2) = 0.4 + 0.175 + 0.25 = 0.825
        # B: 0.40*(5/10) + 0.35*(10/10) + 0.25*(1/2) = 0.2 + 0.35 + 0.125 = 0.675
        assert rankings[0][0] == "A"
        assert abs(rankings[0][1] - 0.825) < 0.01
        assert abs(rankings[1][1] - 0.675) < 0.01

    def test_single_variant_gets_one(self, postforge_root):
        from simulator import SimulationEngine, VariantSimulation, SimulatedMetrics
        engine = self._make_engine(postforge_root)

        results = {
            "A": VariantSimulation(
                variant_id="A",
                metrics=SimulatedMetrics(save_count=5, comment_count=3, avg_thread_depth=1.5),
            ),
        }
        rankings = engine.rank_variants(results)
        assert len(rankings) == 1
        assert abs(rankings[0][1] - 1.0) < 0.01

    def test_empty_results(self, postforge_root):
        from simulator import SimulationEngine
        engine = self._make_engine(postforge_root)
        assert engine.rank_variants({}) == []

    def test_max_variant_scores_one(self, postforge_root):
        """Variant with max saves, comments, and depth should get 1.0."""
        from simulator import SimulationEngine, VariantSimulation, SimulatedMetrics
        engine = self._make_engine(postforge_root)

        results = {
            "A": VariantSimulation(
                variant_id="A",
                metrics=SimulatedMetrics(save_count=20, comment_count=15, avg_thread_depth=3.0),
            ),
            "B": VariantSimulation(
                variant_id="B",
                metrics=SimulatedMetrics(save_count=10, comment_count=8, avg_thread_depth=1.5),
            ),
        }
        rankings = engine.rank_variants(results)
        assert rankings[0][0] == "A"
        assert abs(rankings[0][1] - 1.0) < 0.01
