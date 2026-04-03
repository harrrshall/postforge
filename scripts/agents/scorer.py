#!/usr/bin/env python3
"""Scorer Agent — Score variants on 6 dimensions."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from config_loader import load_json, load_md, save_json, get_postforge_root, get_today
from llm_client import LLMClient


def _extract_variant_text(variant_path: Path) -> str:
    """Extract post text from variant markdown."""
    content = variant_path.read_text()
    if "## Post Text" in content:
        start = content.find("## Post Text") + len("## Post Text")
        end = content.find("## First Comment") if "## First Comment" in content else len(content)
        return content[start:end].strip()
    return ""


def _score_with_llm(llm: LLMClient, variant_text: str, voice_profile: str,
                    algorithm_rules: str) -> dict:
    """Score a variant using LLM. Returns dimension scores dict or None."""
    prompt = f"""Score this LinkedIn post on 6 dimensions (0-100 each).

Post text:
{variant_text[:500]}

Voice profile (match authenticity):
{voice_profile[:200]}

Algorithm rules (check compliance):
{algorithm_rules[:200]}

Return ONLY a JSON object with exactly this structure (no markdown, no explanations):
{{
  "hook_strength": {{"score": <0-100>, "reasoning": "<one sentence>"}},
  "save_worthiness": {{"score": <0-100>, "reasoning": "<one sentence>"}},
  "comment_worthiness": {{"score": <0-100>, "reasoning": "<one sentence>"}},
  "dwell_time_potential": {{"score": <0-100>, "reasoning": "<one sentence>"}},
  "voice_authenticity": {{"score": <0-100>, "reasoning": "<one sentence>"}},
  "algorithm_compliance": {{"score": <0-100>, "reasoning": "<one sentence>"}}
}}
"""

    response = llm.complete("reasoning", prompt, max_tokens=400)
    if not response:
        return None

    try:
        # Try to extract JSON from response
        # Sometimes LLM wraps it in markdown code blocks
        if "```json" in response:
            response = response.split("```json")[1].split("```")[0]
        elif "```" in response:
            response = response.split("```")[1].split("```")[0]

        scores_dict = json.loads(response)
        return scores_dict
    except (json.JSONDecodeError, IndexError):
        return None


def _score_with_simulator(root: Path, date: str) -> dict:
    """Fall back to heuristic simulator scoring."""
    from simulator import SimulationEngine

    engine = SimulationEngine(disable_api=True)
    results = engine.simulate_all_variants(date)

    if not results:
        return None

    scores_dict = {}
    for variant_id, reactions in results.items():
        # Map simulator reactions to dimension scores heuristically
        saves = reactions.get("saves", 0)
        comments = reactions.get("comments", 0)
        likes = reactions.get("likes", 0)
        total = saves + comments + likes

        engagement_rate = (total / 10) * 100 if total > 0 else 0  # Normalize to 0-100

        scores_dict[variant_id] = {
            "hook_strength": {"score": min(95, 50 + engagement_rate), "reasoning": "Heuristic score"},
            "save_worthiness": {"score": min(100, 30 + saves * 5), "reasoning": "Heuristic score"},
            "comment_worthiness": {"score": min(100, 20 + comments * 3), "reasoning": "Heuristic score"},
            "dwell_time_potential": {"score": min(100, 40 + engagement_rate * 0.3), "reasoning": "Heuristic score"},
            "voice_authenticity": {"score": min(85, 70), "reasoning": "Heuristic score"},
            "algorithm_compliance": {"score": min(95, 85), "reasoning": "Heuristic score"},
        }

    return scores_dict


def run(root: Path = None, llm: LLMClient = None, date: str = "") -> Path:
    """
    Score all variants for date. Returns path to scores JSON.

    Args:
        root: PostForge root directory
        llm: LLMClient instance
        date: YYYY-MM-DD date string (today if empty)
    """
    if root is None:
        root = get_postforge_root()
    if llm is None:
        llm = LLMClient()
    if not date:
        date = get_today()

    scores_path = root / "output" / "scores" / f"{date}.json"

    # Idempotency: if scores already exist, return them
    if scores_path.exists():
        return scores_path

    # ─── Load variants ───
    variant_dir = root / "output" / "variants" / date
    if not variant_dir.exists():
        print(f"  No variants found for {date}")
        return scores_path

    variant_files = sorted(variant_dir.glob("variant_*.md"))
    if not variant_files:
        print(f"  No variant files found in {variant_dir}")
        return scores_path

    # ─── Load context ───
    voice_profile = ""
    voice_path = root / "config" / "voice_profile.md"
    if voice_path.exists():
        voice_profile = load_md(voice_path)

    algorithm_rules = ""
    algo_path = root / "config" / "algorithm_rules.md"
    if algo_path.exists():
        algorithm_rules = load_md(algo_path)

    intake = {}
    intake_path = root / "output" / "intakes" / f"{date}.json"
    if intake_path.exists():
        intake = load_json(intake_path)

    topic = intake.get("topic", "Unknown")
    goal = intake.get("goal", {}).get("primary", "saves")

    # ─── Score each variant ───
    variant_scores = {}
    for variant_file in variant_files:
        variant_id = variant_file.stem.replace("variant_", "").upper()
        variant_text = _extract_variant_text(variant_file)

        if llm.available:
            scores = _score_with_llm(llm, variant_text, voice_profile, algorithm_rules)
            if scores:
                variant_scores[variant_id] = scores
                continue

    # ─── Fallback: use simulator if no LLM or LLM failed ───
    if not variant_scores:
        variant_scores = _score_with_simulator(root, date) or {}

    # ─── Compute overall scores and ranking ───
    overall_scores = {}
    for variant_id, dims in variant_scores.items():
        # Weighted average: save_worthiness 0.40, comment 0.35, dwell 0.25
        overall = (
            dims.get("save_worthiness", {}).get("score", 50) * 0.40 +
            dims.get("comment_worthiness", {}).get("score", 50) * 0.35 +
            dims.get("dwell_time_potential", {}).get("score", 50) * 0.25
        )
        overall_scores[variant_id] = round(overall, 2)

    # ─── Build output schema ───
    variants_output = []
    for variant_id in sorted(variant_scores.keys()):
        dims = variant_scores[variant_id]
        variant_file = variant_dir / f"variant_{variant_id.lower()}.md"

        # Extract metadata from variant file
        content = variant_file.read_text()
        variant_type = "Unknown"
        format_ = "text"
        if "## Metadata" in content:
            meta_section = content.split("## Metadata")[1].split("##")[0]
            for line in meta_section.split("\n"):
                if "- Type:" in line:
                    variant_type = line.split("Type:")[1].strip()
                if "- Format:" in line:
                    format_ = line.split("Format:")[1].strip()

        variants_output.append({
            "id": variant_id,
            "type": variant_type,
            "format": format_,
            "overall_score": overall_scores[variant_id],
            "dimension_scores": dims,
            "predicted_engagement": {
                "engagement_rate_range": f"{max(1, overall_scores[variant_id] // 20)}.0-{min(10, (overall_scores[variant_id] // 10) + 2)}.0%",
                "expected_comments": f"{max(5, int(dims.get('comment_worthiness', {}).get('score', 50) / 10))}-{int(dims.get('comment_worthiness', {}).get('score', 50) / 5)}",
                "expected_saves": f"{max(3, int(dims.get('save_worthiness', {}).get('score', 50) / 15))}-{int(dims.get('save_worthiness', {}).get('score', 50) / 5)}",
                "first_hour_velocity": f"{max(2, int(dims.get('hook_strength', {}).get('score', 50) / 15))}-{int(dims.get('hook_strength', {}).get('score', 50) / 10)}",
                "viral_potential": "MEDIUM",
            },
        })

    # ─── Sort by overall score (descending) for ranking ───
    variants_output.sort(key=lambda x: x["overall_score"], reverse=True)
    ranking = [v["id"] for v in variants_output]

    top_3 = {}
    for i, v in enumerate(variants_output[:3], 1):
        top_3[f"{['1st', '2nd', '3rd'][i-1]}"] = {
            "id": v["id"],
            "score": v["overall_score"],
            "why": f"{v['type']} ({v['format']})",
        }

    # ─── Write scores JSON ───
    scores_json = {
        "date": date,
        "topic": topic,
        "goal": goal,
        "scoring_weights_version": 2,
        "variants": variants_output,
        "ranking": ranking,
        "top_3": top_3,
    }

    scores_path.parent.mkdir(parents=True, exist_ok=True)
    save_json(scores_path, scores_json)

    return scores_path


if __name__ == "__main__":
    date = sys.argv[1] if len(sys.argv) > 1 else ""
    if not date:
        from config_loader import get_today
        date = get_today()
    path = run(date=date)
    print(f"  Scores saved: {path}")
