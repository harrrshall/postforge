"""PostForge tool handlers — the code that runs when the LLM calls each tool."""

import json
import os
import subprocess
from datetime import date
from pathlib import Path

POSTFORGE_ROOT = Path(
    os.environ.get(
        "POSTFORGE_ROOT",
        os.path.expanduser(
            "~/Desktop/2026/clawbusiness/linkedin_content/postforge"
        ),
    )
)

RUNNER = POSTFORGE_ROOT / "scripts" / "runner.py"


def _run_cli(args: list[str], timeout: int = 120) -> dict:
    """Run a PostForge CLI command and return structured result."""
    cmd = ["python3", str(RUNNER)] + args
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=str(POSTFORGE_ROOT),
        )
        output = result.stdout.strip()
        error = result.stderr.strip()
        if result.returncode != 0:
            return {"success": False, "error": error or output or f"Exit code {result.returncode}"}
        return {"success": True, "output": output, "stderr": error}
    except subprocess.TimeoutExpired:
        return {"success": False, "error": f"Command timed out after {timeout}s"}
    except FileNotFoundError:
        return {"success": False, "error": f"PostForge not found at {POSTFORGE_ROOT}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def _today() -> str:
    return date.today().isoformat()


def _read_json(path: Path) -> dict | None:
    """Read a JSON file, return None if missing."""
    try:
        return json.loads(path.read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        return None


def postforge_status(args: dict, **kwargs) -> str:
    """System health dashboard."""
    result = _run_cli(["status"])
    if not result["success"]:
        return json.dumps(result)

    # Enrich with structured data
    weights = _read_json(POSTFORGE_ROOT / "config" / "scoring_weights.json")
    history = _read_json(POSTFORGE_ROOT / "memory" / "performance_history.json")
    sprint_log = _read_json(POSTFORGE_ROOT / "memory" / "sprint_log.json")

    return json.dumps({
        "success": True,
        "cli_output": result["output"],
        "weights_loaded": weights is not None,
        "tracked_posts": len(history.get("posts", [])) if history else 0,
        "sprints_completed": len(sprint_log.get("sprints", [])) if sprint_log else 0,
        "postforge_root": str(POSTFORGE_ROOT),
    })


def postforge_generate(args: dict, **kwargs) -> str:
    """Generate LinkedIn post variants."""
    topic = args.get("topic", "").strip()
    if not topic:
        return json.dumps({"success": False, "error": "Topic is required"})

    goal = args.get("goal", "saves")
    cli_args = ["generate", f"--topic={topic}", f"--goal={goal}"]

    if args.get("force"):
        cli_args.append("--force")
    if args.get("auto_select"):
        cli_args.append("--auto-select")

    result = _run_cli(cli_args, timeout=300)
    if not result["success"]:
        return json.dumps(result)

    # Read generated scores if available
    today = _today()
    scores = _read_json(POSTFORGE_ROOT / "output" / "scores" / f"{today}.json")
    variants_dir = POSTFORGE_ROOT / "output" / "variants" / today
    variants_exist = list(variants_dir.glob("variant_*.md")) if variants_dir.exists() else []

    return json.dumps({
        "success": True,
        "cli_output": result["output"],
        "date": today,
        "variants_generated": len(variants_exist),
        "variant_files": [v.name for v in sorted(variants_exist)],
        "scores_available": scores is not None,
        "top_variant": scores.get("ranking", [None])[0] if scores else None,
    })


def postforge_simulate(args: dict, **kwargs) -> str:
    """Run audience simulation."""
    target = args.get("target", "").strip()
    if not target:
        return json.dumps({"success": False, "error": "Target (date or variant path) is required"})

    result = _run_cli(["simulate", target], timeout=180)
    if not result["success"]:
        return json.dumps(result)

    # Try reading simulation output
    sim_date = target if len(target) == 10 else None
    if sim_date:
        sim_data = _read_json(POSTFORGE_ROOT / "output" / "simulations" / f"{sim_date}.json")
    else:
        sim_data = None

    return json.dumps({
        "success": True,
        "cli_output": result["output"],
        "simulation_data": sim_data,
    })


def postforge_learn(args: dict, **kwargs) -> str:
    """Input actual post metrics."""
    post_id = args.get("post_id", "").strip()
    if not post_id:
        return json.dumps({"success": False, "error": "post_id is required (format: YYYY-MM-DD-X)"})

    required = ["impressions", "likes", "comments", "saves", "shares"]
    missing = [f for f in required if f not in args]
    if missing:
        return json.dumps({"success": False, "error": f"Missing required metrics: {', '.join(missing)}"})

    # Build metrics dict
    metrics = {
        "post_id": post_id,
        "impressions": int(args["impressions"]),
        "likes": int(args["likes"]),
        "comments": int(args["comments"]),
        "saves": int(args["saves"]),
        "shares": int(args["shares"]),
        "profile_visits": int(args.get("profile_visits", 0)),
    }

    # Calculate engagement rate
    imp = metrics["impressions"]
    if imp > 0:
        total_eng = metrics["likes"] + metrics["comments"] + metrics["saves"] + metrics["shares"]
        metrics["engagement_rate"] = round(total_eng / imp * 100, 2)
    else:
        metrics["engagement_rate"] = 0.0

    # Append to performance history directly (runner.py learn is interactive)
    history_path = POSTFORGE_ROOT / "memory" / "performance_history.json"
    history = _read_json(history_path) or {"posts": []}

    # Check for duplicate
    existing_ids = [p.get("post_id") for p in history.get("posts", [])]
    if post_id in existing_ids:
        return json.dumps({"success": False, "error": f"Post {post_id} already tracked"})

    history["posts"].append(metrics)
    history_path.parent.mkdir(parents=True, exist_ok=True)
    history_path.write_text(json.dumps(history, indent=2))

    return json.dumps({
        "success": True,
        "post_id": post_id,
        "engagement_rate": metrics["engagement_rate"],
        "total_posts_tracked": len(history["posts"]),
    })


def postforge_sprint_review(args: dict, **kwargs) -> str:
    """Run sprint review and weight recalibration."""
    result = _run_cli(["sprint-review"], timeout=120)
    if not result["success"]:
        return json.dumps(result)

    # Read updated state
    weights = _read_json(POSTFORGE_ROOT / "config" / "scoring_weights.json")
    sprint_log = _read_json(POSTFORGE_ROOT / "memory" / "sprint_log.json")

    return json.dumps({
        "success": True,
        "cli_output": result["output"],
        "current_weights": weights,
        "sprints_completed": len(sprint_log.get("sprints", [])) if sprint_log else 0,
    })


def postforge_scores(args: dict, **kwargs) -> str:
    """Read scoring results for a date."""
    target_date = args.get("date", _today())
    scores_path = POSTFORGE_ROOT / "output" / "scores" / f"{target_date}.json"
    scores = _read_json(scores_path)

    if scores is None:
        return json.dumps({"success": False, "error": f"No scores found for {target_date}"})

    return json.dumps({
        "success": True,
        "date": target_date,
        "scores": scores,
    })


def postforge_read_variant(args: dict, **kwargs) -> str:
    """Read a specific post variant."""
    variant = args.get("variant", "").strip().lower()
    if not variant or variant not in "abcdef":
        return json.dumps({"success": False, "error": "Variant must be a-f"})

    target_date = args.get("date", _today())
    variant_path = POSTFORGE_ROOT / "output" / "variants" / target_date / f"variant_{variant}.md"

    if not variant_path.exists():
        return json.dumps({
            "success": False,
            "error": f"Variant {variant} not found for {target_date}",
            "path": str(variant_path),
        })

    content = variant_path.read_text()
    word_count = len(content.split())

    return json.dumps({
        "success": True,
        "date": target_date,
        "variant": variant,
        "content": content,
        "word_count": word_count,
        "path": str(variant_path),
    })
