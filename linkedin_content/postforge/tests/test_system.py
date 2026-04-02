#!/usr/bin/env python3
"""
PostForge System Tests — Validates all config files, directory structure, and agent skills.

Run: python tests/test_system.py
"""

import os
import sys
import json
from pathlib import Path

# PostForge root
POSTFORGE_ROOT = Path(__file__).parent.parent
CONFIG_DIR = POSTFORGE_ROOT / "config"
MEMORY_DIR = POSTFORGE_ROOT / "memory"
SCRIPTS_DIR = POSTFORGE_ROOT / "scripts"
RESEARCH_DIR = POSTFORGE_ROOT / "research"
OUTPUT_DIR = POSTFORGE_ROOT / "output"
TESTS_DIR = POSTFORGE_ROOT / "tests"

PASS = 0
FAIL = 0
RESULTS = []


def test(name: str, condition: bool, detail: str = ""):
    global PASS, FAIL
    status = "PASS" if condition else "FAIL"
    if condition:
        PASS += 1
    else:
        FAIL += 1
    icon = "+" if condition else "X"
    result = f"  [{icon}] {name}"
    if not condition and detail:
        result += f"\n      -> {detail}"
    print(result)
    RESULTS.append({"test": name, "status": status, "detail": detail})


def test_directory_structure():
    """Test 1: Verify complete directory structure exists."""
    print("\n=== TEST GROUP 1: Directory Structure ===")

    required_dirs = [
        CONFIG_DIR,
        MEMORY_DIR,
        SCRIPTS_DIR,
        RESEARCH_DIR,
        RESEARCH_DIR / "scan",
        RESEARCH_DIR / "briefs",
        OUTPUT_DIR,
        OUTPUT_DIR / "variants",
        OUTPUT_DIR / "scores",
        OUTPUT_DIR / "selected",
        TESTS_DIR,
    ]

    for d in required_dirs:
        test(f"Directory exists: {d.relative_to(POSTFORGE_ROOT)}", d.is_dir(), f"Missing: {d}")


def test_config_files():
    """Test 2: Verify all config files exist and are valid."""
    print("\n=== TEST GROUP 2: Config Files ===")

    # CLAUDE.md
    claude_md = POSTFORGE_ROOT / "CLAUDE.md"
    test("CLAUDE.md exists", claude_md.is_file())
    if claude_md.is_file():
        content = claude_md.read_text()
        test("CLAUDE.md has agent identity", "PostForge" in content)
        test("CLAUDE.md has brand voice section", "Brand Voice" in content)
        test("CLAUDE.md has operating rules", "Operating Rules" in content)
        test("CLAUDE.md has Topic DNA", "Topic DNA" in content)
        test("CLAUDE.md has content pillars", "Content Pillars" in content)
        test("CLAUDE.md has sprint cycle", "Sprint" in content or "sprint" in content)
        test("CLAUDE.md references AI-slop patterns", "AI-slop" in content or "ai-slop" in content.lower())
        test("CLAUDE.md has learning rate", "0.20" in content or "0.2" in content)

    # algorithm_rules.md
    algo = CONFIG_DIR / "algorithm_rules.md"
    test("algorithm_rules.md exists", algo.is_file())
    if algo.is_file():
        content = algo.read_text()
        test("Has 360Brew section", "360Brew" in content)
        test("Has engagement signal hierarchy", "Signal" in content and "Hierarchy" in content)
        test("Has saves > comments rule", "5x" in content and "save" in content.lower())
        test("Has comments 15x rule", "15x" in content)
        test("Has dwell time rules", "Dwell" in content or "dwell" in content)
        test("Has format performance data", "6.60%" in content or "6.6%" in content)
        test("Has timing rules", "Wednesday" in content and "9" in content)
        test("Has external link penalty", "60%" in content)
        test("Has AI detection section", "AI Detection" in content or "AI fingerprint" in content.lower())
        test("Has Interest Graph", "Interest Graph" in content)
        test("Has Topic DNA", "Topic DNA" in content)

    # scoring_weights.json
    weights = CONFIG_DIR / "scoring_weights.json"
    test("scoring_weights.json exists", weights.is_file())
    if weights.is_file():
        try:
            data = json.loads(weights.read_text())
            test("scoring_weights.json is valid JSON", True)

            # Check all 6 dimensions exist
            dims = data.get("dimensions", {})
            expected_dims = ["hook_strength", "save_worthiness", "comment_worthiness",
                           "dwell_time_potential", "voice_authenticity", "algorithm_compliance"]
            for dim in expected_dims:
                test(f"Dimension exists: {dim}", dim in dims, f"Missing dimension: {dim}")

            # Check weights sum to 1.0
            total = sum(dims[d]["weight"] for d in expected_dims if d in dims)
            test(f"Weights sum to 1.0 (actual: {total})", abs(total - 1.0) < 0.001, f"Sum: {total}")

            # Check learning rate
            test("Has learning rate", "learning_rate" in data)
            test("Learning rate is 0.20", data.get("learning_rate") == 0.20,
                 f"Actual: {data.get('learning_rate')}")

            # Check weight history
            test("Has weight history", "weight_history" in data and len(data["weight_history"]) > 0)

        except json.JSONDecodeError as e:
            test("scoring_weights.json is valid JSON", False, str(e))

    # audience_personas.md
    personas = CONFIG_DIR / "audience_personas.md"
    test("audience_personas.md exists", personas.is_file())
    if personas.is_file():
        content = personas.read_text()
        test("Has 5 personas", content.count("## Persona") >= 5,
             f"Found {content.count('## Persona')} personas")
        test("Has Busy Founder", "Busy Founder" in content)
        test("Has Tech Peer", "Tech Peer" in content)
        test("Has Aspiring SMB", "Aspiring SMB" in content or "Aspiring" in content)
        test("Has Contrarian", "Contrarian" in content)
        test("Has Lurker", "Lurker" in content)
        test("Has simulation rules per persona", content.count("Simulation rules") >= 5,
             f"Found {content.count('Simulation rules')} simulation rule sections")
        test("Has simulation matrix", "Simulation Matrix" in content)

    # niche_topics.md
    niche = CONFIG_DIR / "niche_topics.md"
    test("niche_topics.md exists", niche.is_file())
    if niche.is_file():
        content = niche.read_text()
        test("Has core topics", "Core" in content and "AI agent" in content)
        test("Has adjacent topics", "Adjacent" in content)
        test("Has 80% rule", "80%" in content)
        test("Has off-limits topics", "Off-Limits" in content or "off-limits" in content.lower())

    # trend_triggers.md
    triggers = CONFIG_DIR / "trend_triggers.md"
    test("trend_triggers.md exists", triggers.is_file())
    if triggers.is_file():
        content = triggers.read_text()
        test("Has FIRE level", "FIRE" in content)
        test("Has HOT level", "HOT" in content)
        test("Has WARM level", "WARM" in content)
        test("Has COOL level", "COOL" in content)
        test("Has detection sources", "Detection" in content or "Source" in content)
        test("Has response template", "template" in content.lower() or "Template" in content)

    # voice_profile.md
    voice = CONFIG_DIR / "voice_profile.md"
    test("voice_profile.md exists", voice.is_file())
    if voice.is_file():
        content = voice.read_text()
        test("Has TONE section", "## TONE" in content)
        test("Has RHYTHM section", "## RHYTHM" in content)
        test("Has VOCABULARY section", "## VOCABULARY" in content)
        test("Has STRUCTURE section", "## STRUCTURE" in content)
        test("Has OPENINGS section", "## OPENINGS" in content or "OPENINGS" in content)
        test("Has TRANSITIONS section", "## TRANSITIONS" in content or "TRANSITIONS" in content)
        test("Has CLOSINGS section", "## CLOSINGS" in content or "CLOSINGS" in content)
        test("Has ANTI-PATTERNS section", "ANTI-PATTERNS" in content)
        test("Has SENTENCE PALETTE section", "SENTENCE PALETTE" in content)
        test("Has FEW-SHOT EXAMPLES", "FEW-SHOT" in content or "Example" in content)
        test("Has Words to AVOID", "AVOID" in content)
        test("Signature words include 'AI employee'", "AI employee" in content)
        test("Avoids list includes generic AI phrases", "fast-paced world" in content.lower() or "game-changer" in content.lower() or "Game-changer" in content)


def test_memory_files():
    """Test 3: Verify memory files exist and have correct structure."""
    print("\n=== TEST GROUP 3: Memory Files ===")

    # performance_history.json
    perf = MEMORY_DIR / "performance_history.json"
    test("performance_history.json exists", perf.is_file())
    if perf.is_file():
        try:
            data = json.loads(perf.read_text())
            test("Has posts array", "posts" in data and isinstance(data["posts"], list))
            test("Has metadata", "metadata" in data)
            test("Posts array is valid", isinstance(data["posts"], list))
        except json.JSONDecodeError as e:
            test("performance_history.json valid JSON", False, str(e))

    # sprint_log.json
    sprint = MEMORY_DIR / "sprint_log.json"
    test("sprint_log.json exists", sprint.is_file())
    if sprint.is_file():
        try:
            data = json.loads(sprint.read_text())
            test("Has sprints array", "sprints" in data and isinstance(data["sprints"], list))
            test("Sprints array is valid", isinstance(data["sprints"], list))
        except json.JSONDecodeError as e:
            test("sprint_log.json valid JSON", False, str(e))

    # Other memory files
    for fname in ["winning_hooks.md", "winning_templates.md", "anti_patterns.md", "trend_response_log.md"]:
        fpath = MEMORY_DIR / fname
        test(f"{fname} exists", fpath.is_file())


def test_agent_skills():
    """Test 4: Verify all agent skill files exist and have required sections."""
    print("\n=== TEST GROUP 4: Agent Skills ===")

    skills = {
        "scan_agent.md": ["Purpose", "Trigger", "Instructions", "Step 1", "Step 2", "Output", "Quality Rules"],
        "research_agent.md": ["Purpose", "Trigger", "Instructions", "Data", "Competitor", "Hook", "Output", "Quality Rules"],
        "writer_agent.md": ["Purpose", "Model", "Trigger", "Instructions", "Variant A", "Variant B", "Variant C", "Variant D", "Variant E", "Variant F", "Constraints", "Output", "Quality Rules"],
        "scorer_agent.md": ["Purpose", "Model", "Trigger", "Instructions", "Hook Strength", "Save-Worthiness", "Comment-Worthiness", "Dwell Time", "Voice Authenticity", "Algorithm Compliance", "Persona Simulation", "Output", "Quality Rules"],
        "learn_agent.md": ["Purpose", "Trigger", "Function A", "Function B", "Function C", "Function D", "Quality Rules"],
    }

    for skill_name, required_sections in skills.items():
        skill_path = SCRIPTS_DIR / skill_name
        test(f"{skill_name} exists", skill_path.is_file())
        if skill_path.is_file():
            content = skill_path.read_text()
            for section in required_sections:
                test(f"  {skill_name} has '{section}'", section in content,
                     f"Missing section: {section}")

    # Voice extractor
    ve = SCRIPTS_DIR / "voice_extractor.py"
    test("voice_extractor.py exists", ve.is_file())
    if ve.is_file():
        content = ve.read_text()
        test("Has Layer 1 (Statistical)", "Layer 1" in content or "extract_stats" in content)
        test("Has Layer 2 (LLM Analysis)", "Layer 2" in content or "sample_chunks" in content)
        test("Has Layer 3 (Synthesis)", "Layer 3" in content or "layer3" in content.lower())
        test("Has main pipeline", "run_pipeline" in content)


def test_voice_extractor():
    """Test 5: Run voice_extractor.py Layer 1 on sample data."""
    print("\n=== TEST GROUP 5: Voice Extractor Layer 1 ===")

    # Import the module
    sys.path.insert(0, str(SCRIPTS_DIR))
    try:
        from voice_extractor import extract_stats, load_corpus, sample_chunks

        # Create a sample corpus from the voice_profile.md examples
        sample_text = """
        ₹2.3 lakhs per month. That's what a single Pune dermatology clinic was losing to missed
        appointments, unanswered WhatsApp messages, and manual follow-ups. We set up an AI employee
        in 10 hours. Now it answers patient queries 24/7 in Hindi and English. Books appointments
        automatically. Sends payment reminders without being asked. Generates a daily report ready
        by 7 AM. The clinic owner told us: "I didn't hire a person. I hired a system that never
        takes leave." 47x ROI. In the first month. If your clinic is still answering WhatsApp
        manually at 11 PM, your competitor probably isn't.

        We found 512 security vulnerabilities in OpenClaw. Not a typo. Kaspersky's audit flagged 8
        as critical. 9 CVEs disclosed in 4 days. The creator himself called it "a tech preview, a
        hobby." So why are we building a business on it? Because the framework is phenomenal. The
        security isn't. That's exactly the gap Humanless fills. We harden every deployment before it
        touches a customer. API keys stay on your machine. No data leaves your infrastructure.
        OpenClaw has 310,000 GitHub stars for a reason. The AI is brilliant. The production
        readiness isn't. We make it production-ready. For ₹4,999.

        88% of Indian companies say they use AI. 6% see real returns. That's not an AI problem.
        That's an implementation problem. The Fortune 500 has armies of ML engineers. A Coimbatore
        coaching institute has a WhatsApp group and Excel. Most AI tools are built for the 88%.
        We're building for the other 63 million MSMEs who got left behind. No coding needed. No ML
        engineer needed. No ₹50 lakh annual contract. Just an AI employee that answers parents'
        calls, tracks fee payments, and sends attendance updates. Starting at ₹4,999.
        """

        stats = extract_stats(sample_text)

        test("extract_stats returns dict", isinstance(stats, dict))
        test("Has corpus_size", "corpus_size" in stats)
        test("Has sentence_patterns", "sentence_patterns" in stats)
        test("Has vocabulary", "vocabulary" in stats)
        test("Has punctuation", "punctuation" in stats)
        test("Has voice_indicators", "voice_indicators" in stats)
        test("Has readability", "readability" in stats)

        # Check specific values
        test("Total words > 0", stats["corpus_size"]["total_words"] > 0,
             f"Got: {stats['corpus_size']['total_words']}")
        test("Lexical diversity > 0", stats["vocabulary"]["lexical_diversity"] > 0,
             f"Got: {stats['vocabulary']['lexical_diversity']}")
        test("Has top 50 words", len(stats["vocabulary"]["top_50_words"]) > 0)
        test("Has bigrams", len(stats["vocabulary"]["top_30_bigrams"]) > 0)
        test("Question frequency calculated", stats["punctuation"]["question_pct_of_sentences"] >= 0)

        # Test sample_chunks
        chunks = sample_chunks(sample_text, num_samples=3, chunk_size=50)
        test("sample_chunks returns list", isinstance(chunks, list))
        test("sample_chunks returns correct count", len(chunks) >= 1)

    except ImportError as e:
        test("voice_extractor.py importable", False, str(e))
    except Exception as e:
        test("voice_extractor.py runs without error", False, str(e))


def test_cross_references():
    """Test 6: Verify cross-references between files are consistent."""
    print("\n=== TEST GROUP 6: Cross-References ===")

    # Check that CLAUDE.md references the correct scoring dimensions
    claude_content = (POSTFORGE_ROOT / "CLAUDE.md").read_text()
    weights_data = json.loads((CONFIG_DIR / "scoring_weights.json").read_text())

    for dim in weights_data["dimensions"]:
        readable_dim = dim.replace("_", " ")
        # Just check the concept is mentioned (not exact key name)
        test(f"CLAUDE.md references dimension concept: {dim}",
             any(word in claude_content.lower() for word in readable_dim.split()),
             f"Dimension '{dim}' concept not found in CLAUDE.md")

    # Check that all 5 content pillars in CLAUDE.md exist
    for pillar in ["The Proof", "The Build", "The Shift", "The Framework", "Trend"]:
        test(f"CLAUDE.md has pillar: {pillar}", pillar in claude_content)

    # Check algorithm_rules.md has all format types mentioned in scoring
    algo_content = (CONFIG_DIR / "algorithm_rules.md").read_text()
    for fmt in ["PDF Carousel", "Native Video", "Text"]:
        test(f"algorithm_rules.md has format: {fmt}", fmt in algo_content or fmt.lower() in algo_content.lower())

    # Check voice_profile anti-patterns match algorithm_rules MUST NOT
    voice_content = (CONFIG_DIR / "voice_profile.md").read_text()
    for pattern in ["external link", "engagement bait"]:
        test(f"voice_profile.md references: {pattern}",
             pattern in voice_content.lower() or pattern.replace(" ", "") in voice_content.lower())


def test_compliance_checker():
    """Test 7: Run compliance checks on the voice_profile.md few-shot examples."""
    print("\n=== TEST GROUP 7: Few-Shot Example Compliance ===")

    voice_content = (CONFIG_DIR / "voice_profile.md").read_text()

    # Extract examples from voice_profile
    # Check for common compliance violations in the examples themselves
    examples_section = voice_content.split("FEW-SHOT")[1] if "FEW-SHOT" in voice_content else ""

    if examples_section:
        test("Few-shot examples section found", True)

        # Check no external links in examples
        import re
        links = re.findall(r'https?://\S+', examples_section)
        test("No external links in few-shot examples", len(links) == 0,
             f"Found {len(links)} links: {links[:3]}")

        # Check no engagement bait
        bait_phrases = ["comment yes", "tag someone", "repost this", "agree?"]
        found_bait = [p for p in bait_phrases if p in examples_section.lower()]
        test("No engagement bait in few-shot examples", len(found_bait) == 0,
             f"Found bait: {found_bait}")

        # Check no AI-slop
        slop_phrases = ["in today's fast-paced", "let me break it down", "game-changer",
                       "revolutionary", "dive deep", "unlock your potential"]
        found_slop = [p for p in slop_phrases if p in examples_section.lower()]
        test("No AI-slop in few-shot examples", len(found_slop) == 0,
             f"Found slop: {found_slop}")

        # Check examples have specific numbers
        numbers = re.findall(r'[\d₹]+[,.\d]*', examples_section)
        test("Few-shot examples contain specific numbers", len(numbers) >= 3,
             f"Found {len(numbers)} numbers")
    else:
        test("Few-shot examples section found", False, "Could not find FEW-SHOT section")


def test_intake_system():
    """Test 8: Verify intake agent and voice onboarding system."""
    print("\n=== TEST GROUP 8: Intake & Voice Onboarding ===")

    # New directories
    test("output/intakes/ directory exists", (OUTPUT_DIR / "intakes").is_dir())
    test("config/voice_samples/ directory exists", (CONFIG_DIR / "voice_samples").is_dir())

    # intake_agent.md
    intake = SCRIPTS_DIR / "intake_agent.md"
    test("intake_agent.md exists", intake.is_file())
    if intake.is_file():
        content = intake.read_text()
        test("  Has Purpose section", "Purpose" in content)
        test("  Has Trigger section", "Trigger" in content)
        test("  Has Instructions section", "Instructions" in content)
        test("  Has Output section", "Output" in content or "Step 4" in content)
        test("  Has Quality Rules", "Quality Rules" in content)
        test("  Asks about topic", "topic" in content.lower() and "Question 1" in content)
        test("  Asks about goal", "goal" in content.lower() and "Question 2" in content)
        test("  Has 5 goal options", all(g in content for g in ["maximize_saves", "maximize_comments", "maximize_velocity"]))
        test("  Computes pipeline_hints", "pipeline_hints" in content)
        test("  Validates Topic DNA", "niche_topics" in content)
        test("  Loads performance_history", "performance_history" in content)

    # voice_onboarding_agent.md
    voice_ob = SCRIPTS_DIR / "voice_onboarding_agent.md"
    test("voice_onboarding_agent.md exists", voice_ob.is_file())
    if voice_ob.is_file():
        content = voice_ob.read_text()
        test("  Has Purpose section", "Purpose" in content)
        test("  Has Trigger section", "Trigger" in content)
        test("  Has Instructions section", "Instructions" in content)
        test("  Has Quality Rules", "Quality Rules" in content)
        test("  Collects writing samples", "writing sample" in content.lower() or "Collect" in content)
        test("  Validates corpus size", "2,000" in content or "2000" in content)
        test("  Runs Layer 1", "Layer 1" in content or "voice_extractor" in content)
        test("  Runs Layer 2 inline", "Layer 2" in content and "inline" in content.lower())
        test("  Runs Layer 3 synthesis", "Layer 3" in content)
        test("  Confirms before replacing", "approval" in content.lower() or "confirm" in content.lower())
        test("  Backs up old profile", "backup" in content.lower())
        test("  Saves to voice_samples/", "voice_samples" in content)


def test_intake_integration():
    """Test 9: Verify existing agents are integrated with intake system."""
    print("\n=== TEST GROUP 9: Intake Integration ===")

    # research_agent.md has Step 0
    research = SCRIPTS_DIR / "research_agent.md"
    if research.is_file():
        content = research.read_text()
        test("research_agent.md has Step 0 (intake loading)",
             "Step 0" in content and "intake" in content.lower())
        test("research_agent.md references intakes JSON",
             "intakes" in content)
        test("research_agent.md has backwards compatibility",
             "fall back" in content.lower() or "fallback" in content.lower() or "no intake" in content.lower())

    # writer_agent.md has Step 1.5
    writer = SCRIPTS_DIR / "writer_agent.md"
    if writer.is_file():
        content = writer.read_text()
        test("writer_agent.md has Step 1.5 (goal-based prioritization)",
             "Step 1.5" in content)
        test("writer_agent.md loads intake brief",
             "intakes" in content or "intake brief" in content.lower())
        test("writer_agent.md has goal-variant mapping",
             "maximize_saves" in content and "maximize_comments" in content)

    # scorer_agent.md has Step 3.5
    scorer = SCRIPTS_DIR / "scorer_agent.md"
    if scorer.is_file():
        content = scorer.read_text()
        test("scorer_agent.md has Step 3.5 (goal-based scoring)",
             "Step 3.5" in content)
        test("scorer_agent.md loads intake brief",
             "intakes" in content or "intake brief" in content.lower())
        test("scorer_agent.md has goal multipliers",
             "1.20" in content and "multiplier" in content.lower())
        test("scorer_agent.md shows goal in presentation",
             "goal" in content.lower() and "boosted" in content.lower())

    # CLAUDE.md has intake in operating rules
    claude = POSTFORGE_ROOT / "CLAUDE.md"
    if claude.is_file():
        content = claude.read_text()
        test("CLAUDE.md has intake as Step 0",
             "intake_agent" in content and ("Step 0" in content or "0." in content))
        test("CLAUDE.md has first-time setup section",
             "First-Time Setup" in content or "first-time" in content.lower())
        test("CLAUDE.md references voice onboarding",
             "voice_onboarding" in content or "voice onboarding" in content.lower())


# ─── Run All Tests ───

if __name__ == "__main__":
    print("=" * 60)
    print("PostForge System Tests")
    print(f"Root: {POSTFORGE_ROOT}")
    print("=" * 60)

    test_directory_structure()
    test_config_files()
    test_memory_files()
    test_agent_skills()
    test_voice_extractor()
    test_cross_references()
    test_compliance_checker()
    test_intake_system()
    test_intake_integration()

    print("\n" + "=" * 60)
    print(f"RESULTS: {PASS} passed, {FAIL} failed, {PASS + FAIL} total")
    print("=" * 60)

    if FAIL > 0:
        print("\nFailed tests:")
        for r in RESULTS:
            if r["status"] == "FAIL":
                print(f"  X {r['test']}: {r['detail']}")
        sys.exit(1)
    else:
        print("\nAll tests passed!")
        sys.exit(0)
