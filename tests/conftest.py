"""
PostForge Test Fixtures — Shared fixtures for all test modules.

Key design: monkeypatch `get_postforge_root` so all tests use tmp_path,
never touching production data.
"""

import json
import sys
from pathlib import Path

import pytest

# Ensure scripts is importable
SCRIPTS_DIR = Path(__file__).parent.parent / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))


# ─── Core Fixtures ───


@pytest.fixture
def postforge_root(tmp_path, monkeypatch):
    """Create full PostForge directory tree in tmp_path and monkeypatch root."""
    dirs = [
        "config", "config/voice_samples",
        "memory",
        "research/scan", "research/briefs",
        "output/variants", "output/scores", "output/selected",
        "output/intakes", "output/simulations",
        "logs", "tests",
    ]
    for d in dirs:
        (tmp_path / d).mkdir(parents=True, exist_ok=True)

    import config_loader
    monkeypatch.setattr(config_loader, "get_postforge_root", lambda: tmp_path)

    # Also patch modules that import get_postforge_root via `from config_loader import ...`
    # (Python copies the reference, so patching config_loader alone isn't enough)
    for mod_name in ["simulator", "auto_learn", "runner", "llm_client"]:
        try:
            mod = __import__(mod_name)
            if hasattr(mod, "get_postforge_root"):
                monkeypatch.setattr(mod, "get_postforge_root", lambda: tmp_path)
        except ImportError:
            pass

    # Write a minimal provider.json so LLMClient can load config
    provider_config = {
        "default_provider": "anthropic",
        "providers": {
            "anthropic": {
                "sdk": "anthropic",
                "api_key_env": "ANTHROPIC_API_KEY",
                "models": {"reasoning": "test-model", "writing": "test-model", "fast": "test-model"},
            }
        },
    }
    _write_json(tmp_path / "config" / "provider.json", provider_config)

    return tmp_path


@pytest.fixture
def freeze_today(monkeypatch):
    """Freeze get_today() to return a fixed date across all modules."""
    import config_loader
    monkeypatch.setattr(config_loader, "get_today", lambda: "2026-04-15")

    # Patch modules that imported get_today via `from config_loader import get_today`
    for mod_name in ["runner", "simulator", "auto_learn"]:
        try:
            mod = __import__(mod_name)
            if hasattr(mod, "get_today"):
                monkeypatch.setattr(mod, "get_today", lambda: "2026-04-15")
        except ImportError:
            pass

    return "2026-04-15"


# ─── Sample Data Fixtures ───


@pytest.fixture
def sample_scoring_weights():
    """Return v1 scoring weights with known values summing to 1.0."""
    return {
        "version": 1,
        "dimensions": {
            "hook_strength": {"weight": 0.25, "description": "First 150 chars scroll-stopping power"},
            "save_worthiness": {"weight": 0.25, "description": "Bookmark-worthy reference value"},
            "comment_worthiness": {"weight": 0.20, "description": "Debate potential, CTA quality"},
            "dwell_time_potential": {"weight": 0.15, "description": "Read time, progressive revelation"},
            "voice_authenticity": {"weight": 0.10, "description": "Matches voice_profile.md"},
            "algorithm_compliance": {"weight": 0.05, "description": "No links, no bait, Topic DNA"},
        },
        "learning_rate": 0.20,
        "total_calibration_posts": 0,
        "weight_history": [
            {
                "version": 1,
                "date": "2026-04-01",
                "weights": {
                    "hook_strength": 0.25,
                    "save_worthiness": 0.25,
                    "comment_worthiness": 0.20,
                    "dwell_time_potential": 0.15,
                    "voice_authenticity": 0.10,
                    "algorithm_compliance": 0.05,
                },
                "reason": "Initial weights for testing",
            }
        ],
    }


def _make_post(post_id, date, variant_type, fmt, pillar, hook,
               engagement_rate, impressions, likes, comments, saves, shares,
               pred_rate_range, pred_comments, pred_saves,
               outcome, dimension_scores):
    """Helper to build a post entry matching the performance_history schema."""
    total = likes + comments + saves + shares
    actual_rate = (total / impressions * 100) if impressions > 0 else 0

    # Calculate prediction accuracy
    pred_parts = pred_rate_range.replace("%", "").split("-")
    pred_mid = (float(pred_parts[0]) + float(pred_parts[1])) / 2
    rate_acc = max(0, 1 - abs(actual_rate - pred_mid) / max(pred_mid, 0.01))

    pred_c_parts = str(pred_comments).split("-")
    pred_c_mid = (int(pred_c_parts[0]) + int(pred_c_parts[1])) / 2
    comment_acc = max(0, 1 - abs(comments - pred_c_mid) / max(pred_c_mid, 1))

    pred_s_parts = str(pred_saves).split("-")
    pred_s_mid = (int(pred_s_parts[0]) + int(pred_s_parts[1])) / 2
    save_acc = max(0, 1 - abs(saves - pred_s_mid) / max(pred_s_mid, 1))

    return {
        "post_id": post_id,
        "date_posted": date,
        "variant_type": variant_type,
        "format": fmt,
        "pillar": pillar,
        "hook_text": hook,
        "posting_time": "manual entry",
        "predicted": {
            "engagement_rate_range": pred_rate_range,
            "expected_comments": pred_comments,
            "expected_saves": pred_saves,
        },
        "actual_24h": {
            "impressions": impressions,
            "likes": likes,
            "comments": comments,
            "saves": saves,
            "shares": shares,
            "profile_visits": 50,
            "engagement_rate": f"{actual_rate:.2f}%",
            "first_hour_comments": comments // 2,
            "comment_quality": "substantive",
        },
        "actual_7d": None,
        "prediction_accuracy": {
            "engagement_rate": round(rate_acc, 3),
            "comments": round(comment_acc, 3),
            "saves": round(save_acc, 3),
        },
        "outcome": outcome,
        "dimension_scores_at_time": dimension_scores,
    }


@pytest.fixture
def sample_performance_history():
    """Return performance history with 3 posts having controlled metrics."""
    posts = [
        _make_post(
            "2026-04-10-A", "2026-04-10", "Contrarian Take", "text", "shift",
            "88% of Indian companies say they use AI. 6% see real returns.",
            engagement_rate=3.5, impressions=8000, likes=150, comments=25, saves=30, shares=8,
            pred_rate_range="3.0-5.0%", pred_comments="10-22", pred_saves="8-20",
            outcome="MATCHED",
            dimension_scores={
                "hook_strength": 85, "save_worthiness": 60,
                "comment_worthiness": 88, "dwell_time_potential": 70,
                "voice_authenticity": 75, "algorithm_compliance": 90,
            },
        ),
        _make_post(
            "2026-04-11-D", "2026-04-11", "Framework", "carousel", "framework",
            "78M Indian MSMEs. Under 5% use AI agents.",
            engagement_rate=5.0, impressions=10000, likes=200, comments=35, saves=50, shares=12,
            pred_rate_range="4.0-6.0%", pred_comments="15-30", pred_saves="20-40",
            outcome="MATCHED",
            dimension_scores={
                "hook_strength": 80, "save_worthiness": 95,
                "comment_worthiness": 70, "dwell_time_potential": 85,
                "voice_authenticity": 80, "algorithm_compliance": 92,
            },
        ),
        _make_post(
            "2026-04-12-B", "2026-04-12", "Data Story", "text", "proof",
            "₹2.3 lakhs per month. That's what a Pune clinic was losing.",
            engagement_rate=2.0, impressions=6000, likes=60, comments=10, saves=8, shares=3,
            pred_rate_range="3.5-5.5%", pred_comments="12-24", pred_saves="10-25",
            outcome="UNDERPERFORMED",
            dimension_scores={
                "hook_strength": 90, "save_worthiness": 55,
                "comment_worthiness": 45, "dwell_time_potential": 60,
                "voice_authenticity": 85, "algorithm_compliance": 88,
            },
        ),
    ]

    total_eng = sum(
        p["actual_24h"]["likes"] + p["actual_24h"]["comments"] +
        p["actual_24h"]["saves"] + p["actual_24h"]["shares"]
        for p in posts
    )
    all_accs = [p["prediction_accuracy"]["engagement_rate"] for p in posts]

    return {
        "posts": posts,
        "metadata": {
            "total_posts_tracked": 3,
            "total_engagements": total_eng,
            "avg_prediction_accuracy": sum(all_accs) / len(all_accs),
        },
    }


@pytest.fixture
def sample_sprint_log_empty():
    """Return empty sprint log."""
    return {
        "sprints": [],
        "metadata": {"total_sprints": 0, "current_sprint": 0},
    }


@pytest.fixture
def sample_sprint_log_with_one():
    """Return sprint log with one completed sprint."""
    return {
        "sprints": [
            {
                "sprint_number": 1,
                "dates": "2026-04-01 to 2026-04-03",
                "posts_published": 3,
                "total_engagements": 500,
                "avg_engagement_rate": "3.0%",
                "best_performing": {"post_id": "2026-04-02-B", "engagement_rate": "3.5%", "why": "Data Story text"},
                "worst_performing": {"post_id": "2026-04-01-A", "engagement_rate": "2.5%", "why": "Contrarian text"},
                "scoring_weight_changes": {},
                "patterns_extracted": {"winning_hooks": 0, "anti_patterns": 1},
                "prediction_accuracy_this_sprint": 0.65,
                "learning_rate_used": 0.10,
            }
        ],
        "metadata": {"total_sprints": 1, "current_sprint": 1},
    }


@pytest.fixture
def populated_postforge(postforge_root, sample_scoring_weights, sample_performance_history,
                        sample_sprint_log_empty, freeze_today):
    """Write all fixture data to tmp dir. Returns root path."""
    root = postforge_root

    # Write config
    _write_json(root / "config" / "scoring_weights.json", sample_scoring_weights)

    # Write memory
    _write_json(root / "memory" / "performance_history.json", sample_performance_history)
    _write_json(root / "memory" / "sprint_log.json", sample_sprint_log_empty)
    (root / "memory" / "winning_hooks.md").write_text("# Winning Hooks\n")
    (root / "memory" / "winning_templates.md").write_text("# Winning Templates\n")
    (root / "memory" / "anti_patterns.md").write_text("# Anti-Patterns\n")
    (root / "memory" / "trend_response_log.md").write_text("# Trend Response Log\n")

    # Write a sample variant
    variant_dir = root / "output" / "variants" / "2026-04-15"
    variant_dir.mkdir(parents=True, exist_ok=True)
    (variant_dir / "variant_a.md").write_text(SAMPLE_VARIANT_A)
    (variant_dir / "variant_b.md").write_text(SAMPLE_VARIANT_B)

    # Write sample scores
    _write_json(root / "output" / "scores" / "2026-04-15.json", SAMPLE_SCORES)

    # Write audience_personas.md (needed by simulator)
    (root / "config" / "audience_personas.md").write_text("# Audience Personas\n## Persona 1: Busy Founder\n")

    return root


def _write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


# ─── Sample Content ───


SAMPLE_VARIANT_A = """# Variant A: Contrarian Take

## Metadata
- Type: Contrarian Take
- Format: text
- Pillar: shift
- Word count: 250
- Primary engagement target: comments

## Hook Analysis
- First 150 chars: "88% of Indian companies say they use AI. 6% see real returns. That's not an AI problem."
- Hook pattern: number/contrast

## Post Text
88% of Indian companies say they use AI. 6% see real returns.

That's not an AI problem. That's an implementation problem.

The Fortune 500 has armies of ML engineers. A Coimbatore coaching institute has a WhatsApp group and Excel.

Most AI tools are built for the 88%. We're building for the other 63 million MSMEs who got left behind.

No coding needed. No ML engineer needed. No ₹50 lakh annual contract.

Just an AI employee that answers parents' calls, tracks fee payments, and sends attendance updates.

Starting at ₹4,999.

## First Comment
#AIAgents #IndianSMB #MSMEDigitization
"""

SAMPLE_VARIANT_B = """# Variant B: Data Story

## Metadata
- Type: Data Story
- Format: carousel
- Pillar: proof
- Word count: 280
- Primary engagement target: saves

## Hook Analysis
- First 150 chars: "₹2.3 lakhs per month. That's what a single Pune dermatology clinic was losing to missed appointments."
- Hook pattern: number/story

## Post Text
₹2.3 lakhs per month. That's what a single Pune dermatology clinic was losing to missed appointments, unanswered WhatsApp messages, and manual follow-ups.

We set up an AI employee in 10 hours.

Now it answers patient queries 24/7 in Hindi and English. Books appointments automatically. Sends payment reminders without being asked.

The clinic owner told us: "I didn't hire a person. I hired a system that never takes leave."

47x ROI. In the first month.

If your clinic is still answering WhatsApp manually at 11 PM, your competitor probably isn't.

## First Comment
#HealthcareAI #AIEmployee #IndianSMB
"""

SAMPLE_SCORES = {
    "date": "2026-04-15",
    "topic": "AI adoption for Indian MSMEs",
    "scoring_weights_version": 1,
    "variants": [
        {
            "id": "A",
            "type": "Contrarian Take",
            "format": "text",
            "overall_score": 79.65,
            "dimension_scores": {
                "hook_strength": {"score": 85, "reasoning": "Strong number contrast"},
                "save_worthiness": {"score": 60, "reasoning": "Low reference value"},
                "comment_worthiness": {"score": 88, "reasoning": "Provocative claim"},
                "dwell_time_potential": {"score": 70, "reasoning": "Medium length"},
                "voice_authenticity": {"score": 75, "reasoning": "Good match"},
                "algorithm_compliance": {"score": 90, "reasoning": "No violations"},
            },
            "predicted_engagement": {
                "engagement_rate_range": "3.0-5.0%",
                "expected_comments": "10-22",
                "expected_saves": "4-10",
                "first_hour_velocity": "6-12 comments",
                "viral_potential": "MEDIUM",
            },
        },
        {
            "id": "B",
            "type": "Data Story",
            "format": "carousel",
            "overall_score": 83.10,
            "dimension_scores": {
                "hook_strength": {"score": 90, "reasoning": "Specific rupee amount"},
                "save_worthiness": {"score": 80, "reasoning": "Case study data"},
                "comment_worthiness": {"score": 65, "reasoning": "Story, less debate"},
                "dwell_time_potential": {"score": 85, "reasoning": "Carousel format"},
                "voice_authenticity": {"score": 80, "reasoning": "Strong voice match"},
                "algorithm_compliance": {"score": 92, "reasoning": "No violations"},
            },
            "predicted_engagement": {
                "engagement_rate_range": "4.0-6.0%",
                "expected_comments": "8-18",
                "expected_saves": "15-30",
                "first_hour_velocity": "4-8 comments",
                "viral_potential": "MEDIUM",
            },
        },
    ],
    "ranking": ["B", "A"],
    "top_3": {
        "1st": {"id": "B", "score": 83.10, "why": "Strong data story with carousel"},
        "2nd": {"id": "A", "score": 79.65, "why": "Provocative contrarian take"},
    },
}
