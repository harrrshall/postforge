#!/usr/bin/env python3
"""
PostForge Simulation Engine — Multi-agent LinkedIn post simulation.

Spawns virtual persona agents that react to post variants, generate comments,
and create emergent debate threads. Uses LLM API (fast tier) for persona agents.

Falls back to local heuristic simulation if no LLM provider is configured.

Usage:
    python scripts/simulator.py <variant_path>
    python scripts/simulator.py --all <date>  # simulate all variants for a date
"""

import sys
import json
import os
import re
import random
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, field, asdict

sys.path.insert(0, str(Path(__file__).parent))

from config_loader import (
    get_postforge_root, get_today, load_json, save_json, load_md,
)


# ─── Data Classes ───

@dataclass
class PersonaReaction:
    persona_name: str
    action: str  # SKIP, SKIM, READ, LIKE, COMMENT, SAVE, SHARE
    probability: int  # 0-100
    reasoning: str
    comment_text: str | None = None
    dwell_seconds: int = 0


@dataclass
class ThreadReply:
    author: str
    replying_to: str
    text: str
    round_num: int


@dataclass
class SimulatedMetrics:
    engagement_rate: float = 0.0
    comment_count: int = 0
    avg_thread_depth: float = 0.0
    save_count: int = 0
    share_count: int = 0
    like_count: int = 0
    avg_dwell_seconds: float = 0.0
    debate_heat_score: float = 0.0  # replies × disagreement ratio


@dataclass
class VariantSimulation:
    variant_id: str
    reactions: list = field(default_factory=list)
    thread_replies: list = field(default_factory=list)
    metrics: SimulatedMetrics = field(default_factory=SimulatedMetrics)
    composite_score: float = 0.0
    top_comments: list = field(default_factory=list)
    thread_preview: str = ""


# ─── Persona Definitions ───

def load_personas() -> list[dict]:
    """Load and expand personas from audience_personas.md into 10 persona dicts."""
    root = get_postforge_root()
    personas_md = load_md(root / "config" / "audience_personas.md")

    # Base 5 personas with expanded attributes
    base_personas = [
        {
            "name": "busy_founder_pragmatic",
            "display": "Busy Founder (Pragmatic)",
            "role": "Founder, 10-50 employees, Tier 1 Indian city",
            "scroll_speed": "fast",
            "stops_for": "Bold ROI claims with specific numbers",
            "comment_style": "short, practical, ROI-focused",
            "save_threshold": "actionable frameworks with rupee math",
            "skip_threshold": "generic advice, long text without numbers",
        },
        {
            "name": "busy_founder_skeptic",
            "display": "Busy Founder (Skeptical)",
            "role": "Founder, 10-50 employees, experienced, seen hype before",
            "scroll_speed": "fast",
            "stops_for": "Claims that seem too good, wants to verify",
            "comment_style": "questioning, asks for proof",
            "save_threshold": "only if data is verifiable",
            "skip_threshold": "anything that sounds like marketing",
        },
        {
            "name": "tech_peer_builder",
            "display": "Tech Peer (Builder)",
            "role": "Developer/AI practitioner, builds with AI daily",
            "scroll_speed": "medium",
            "stops_for": "Technical depth, novel architecture, code patterns",
            "comment_style": "adds nuance, shares own experience, 20+ words",
            "save_threshold": "technical frameworks, architecture decisions",
            "skip_threshold": "surface-level AI hype",
        },
        {
            "name": "tech_peer_critic",
            "display": "Tech Peer (Critical)",
            "role": "Senior dev, skeptical of AI claims, values rigor",
            "scroll_speed": "medium",
            "stops_for": "Bold technical claims to challenge",
            "comment_style": "challenges assumptions, provides counter-examples",
            "save_threshold": "genuinely novel technical insight",
            "skip_threshold": "marketing dressed as tech content",
        },
        {
            "name": "aspiring_smb_eager",
            "display": "Aspiring SMB Owner (Eager)",
            "role": "Small shop/clinic in Tier 2 city, wants to learn about AI",
            "scroll_speed": "slow",
            "stops_for": "Simple explanations, step-by-step guides",
            "comment_style": "asks questions: How much? Does it work in Hindi?",
            "save_threshold": "every framework and checklist",
            "skip_threshold": "jargon-heavy, enterprise-focused",
        },
        {
            "name": "aspiring_smb_cautious",
            "display": "Aspiring SMB Owner (Cautious)",
            "role": "Coaching center owner, interested but budget-conscious",
            "scroll_speed": "slow",
            "stops_for": "Specific cost/benefit with Indian context",
            "comment_style": "asks about pricing and implementation",
            "save_threshold": "ROI calculators, pricing comparisons",
            "skip_threshold": "anything without clear cost info",
        },
        {
            "name": "contrarian_veteran",
            "display": "Contrarian (Industry Veteran)",
            "role": "30-50, consultant, 5000+ followers, loves debate",
            "scroll_speed": "medium-fast",
            "stops_for": "Bold claims, controversial opinions",
            "comment_style": "disagrees, adds nuance, 30+ words with counter-examples",
            "save_threshold": "rarely saves (unless data for counter-argument)",
            "skip_threshold": "posts too agreeable, no edge",
        },
        {
            "name": "contrarian_academic",
            "display": "Contrarian (Academic/Researcher)",
            "role": "AI researcher, values evidence over opinion",
            "scroll_speed": "medium",
            "stops_for": "Unsubstantiated claims to correct",
            "comment_style": "corrects with data, cites research",
            "save_threshold": "well-sourced data compilations",
            "skip_threshold": "opinion without evidence",
        },
        {
            "name": "lurker_passive",
            "display": "Silent Lurker (Passive)",
            "role": "Reads everything in feed, almost never engages",
            "scroll_speed": "slow-medium",
            "stops_for": "Anything in interest area that looks valuable",
            "comment_style": "almost never comments (1% probability)",
            "save_threshold": "exceptional content only (5% probability)",
            "skip_threshold": "weak hook (2 second test)",
        },
        {
            "name": "lurker_saver",
            "display": "Silent Lurker (Saves Quietly)",
            "role": "Reads and saves, never comments, collects resources",
            "scroll_speed": "slow",
            "stops_for": "Reference material, frameworks, data",
            "comment_style": "never comments",
            "save_threshold": "any structured framework or data set",
            "skip_threshold": "opinion pieces without data",
        },
    ]

    return base_personas


# ─── Heuristic Simulation (No API needed) ───

def _maybe(probability: int) -> bool:
    """Return True based on probability (0-100)."""
    return random.random() * 100 < probability


def heuristic_simulate_persona(persona: dict, post_text: str, post_format: str) -> PersonaReaction:
    """Simulate persona reaction using rule-based heuristics."""
    name = persona["name"]
    text_lower = post_text.lower()
    word_count = len(post_text.split())

    # Score features (including hook analysis)
    hook_text = post_text[:150]
    body_text = post_text[150:]

    has_numbers = bool(re.findall(r'[\d₹]+[,.\d]*', post_text))
    has_numbers_in_hook = bool(re.findall(r'[\d₹]+[,.\d]*', hook_text))
    has_question = "?" in post_text
    has_framework = any(w in text_lower for w in ["step", "framework", "checklist", "how to", "guide"])
    has_bold_claim = any(w in text_lower for w in ["most people", "nobody", "everyone", "wrong", "myth", "truth"])
    has_bold_claim_in_hook = any(w in hook_text.lower() for w in ["most people", "nobody", "everyone", "wrong", "myth", "truth"])
    has_indian_context = any(w in text_lower for w in ["india", "msme", "rupee", "₹", "whatsapp", "pune", "jaipur", "mumbai"])
    has_indian_in_hook = any(w in hook_text.lower() for w in ["india", "msme", "rupee", "₹", "whatsapp", "pune", "jaipur", "mumbai"])
    has_data = any(w in text_lower for w in ["%", "million", "billion", "study", "research", "data"])
    is_carousel = post_format == "carousel"

    # Branching by FULL persona name (all 5 paired personas)

    # ─── Busy Founder (Pragmatic) ───
    if name == "busy_founder_pragmatic":
        if has_numbers_in_hook and has_indian_in_hook:
            action = "SAVE" if has_framework else "READ"
            prob = 65 if has_framework else 55
            dwell = 35 if action == "SAVE" else 25
        elif has_numbers and has_indian_context:
            action = "SAVE" if has_framework else "READ"
            prob = 60 if has_framework else 50
            dwell = 30 if action == "SAVE" else 20
        elif has_bold_claim:
            action = "SKIM"
            prob = 50
            dwell = 10
        else:
            action = "SKIP"
            prob = 70
            dwell = 2

    # ─── Busy Founder (Skeptic) ───
    elif name == "busy_founder_skeptic":
        if has_bold_claim_in_hook or has_bold_claim:
            action = "COMMENT"
            prob = 70
            dwell = 25
        elif has_numbers and has_indian_context:
            action = "READ"
            prob = 55
            dwell = 15
        else:
            action = "SKIP"
            prob = 75
            dwell = 2

    # ─── Tech Peer (Builder) ───
    elif name == "tech_peer_builder":
        if has_data and has_framework:
            action = "SAVE"
            prob = 70
            dwell = 35
        elif has_data and has_bold_claim:
            action = "COMMENT"
            prob = 65
            dwell = 30
        elif has_framework:
            action = "SAVE"
            prob = 55
            dwell = 28
        elif has_bold_claim:
            action = "COMMENT"
            prob = 50
            dwell = 20
        else:
            action = "SKIM"
            prob = 50
            dwell = 12

    # ─── Tech Peer (Critic) ───
    elif name == "tech_peer_critic":
        if has_bold_claim:
            action = "COMMENT"
            prob = 80
            dwell = 35
        elif has_data:
            action = "COMMENT"
            prob = 65
            dwell = 25
        else:
            action = "SKIP"
            prob = 60
            dwell = 5

    # ─── Aspiring SMB (Eager) ───
    elif name == "aspiring_smb_eager":
        if has_framework and has_indian_context:
            action = "SAVE"
            prob = 85
            dwell = 55
        elif has_numbers and has_indian_context:
            action = "READ"
            prob = 75
            dwell = 40
        elif has_framework:
            action = "SAVE"
            prob = 70
            dwell = 45
        else:
            action = "READ"
            prob = 60
            dwell = 30

    # ─── Aspiring SMB (Cautious) ───
    elif name == "aspiring_smb_cautious":
        if has_numbers and has_indian_context:
            action = "SAVE"
            prob = 75
            dwell = 45
        elif has_framework:
            action = "READ"
            prob = 65
            dwell = 40
        else:
            action = "READ"
            prob = 50
            dwell = 25

    # ─── Contrarian (Veteran) ───
    elif name == "contrarian_veteran":
        if has_bold_claim:
            action = "COMMENT"
            prob = 90
            dwell = 45
        elif has_data:
            action = "COMMENT"
            prob = 65
            dwell = 35
        else:
            action = "SKIP"
            prob = 55
            dwell = 5

    # ─── Contrarian (Academic) ───
    elif name == "contrarian_academic":
        if has_bold_claim and not has_data:
            action = "COMMENT"
            prob = 85
            dwell = 40
        elif has_data:
            action = "SAVE"
            prob = 60
            dwell = 35
        else:
            action = "SKIP"
            prob = 70
            dwell = 5

    # ─── Lurker (Passive) ───
    elif name == "lurker_passive":
        if is_carousel:
            action = "READ"
            prob = 85
            dwell = 70
        elif has_framework or has_data:
            action = "READ"
            prob = 70
            dwell = 50
        else:
            action = "READ"
            prob = 60
            dwell = 30

    # ─── Lurker (Saver) ───
    elif name == "lurker_saver":
        if has_framework or has_data:
            action = "SAVE"
            prob = 75
            dwell = 50
        elif is_carousel:
            action = "READ"
            prob = 80
            dwell = 70
        else:
            action = "READ"
            prob = 55
            dwell = 30

    else:
        action = "SKIM"
        prob = 50
        dwell = 10

    # Carousel boost
    if is_carousel:
        dwell = int(dwell * 1.5)
        if action == "READ" and has_framework and "saver" in name or "aspiring" in name:
            action = "SAVE"

    # Generate comment text for COMMENT actions with varied templates
    comment_text = None
    if action == "COMMENT":
        # Extract topic keywords for personalization
        topic_keywords = []
        if "whatsapp" in text_lower:
            topic_keywords.append("WhatsApp")
        if "clinic" in text_lower or "healthcare" in text_lower:
            topic_keywords.append("clinic")
        if "automation" in text_lower:
            topic_keywords.append("automation")
        if "python" in text_lower or "code" in text_lower or "api" in text_lower:
            topic_keywords.append("technical")
        if "cost" in text_lower or "price" in text_lower or "rupee" in text_lower:
            topic_keywords.append("cost")

        if name == "busy_founder_skeptic":
            skeptic_comments = [
                "This sounds promising but what's the actual ROI? Have you compared against just hiring?",
                "The numbers look good but what's hidden in the implementation costs?",
                "Bold claim, but where's the third-party validation? Any case studies with similar contexts?",
                "Interesting, but we've seen AI projects fail on exactly these assumptions. How do you mitigate?",
            ]
            comment_text = random.choice(skeptic_comments)

        elif name == "tech_peer_builder":
            builder_comments = [
                "Have you considered the edge cases? The user intent classification is usually where these fail.",
                "We built something similar using a multi-step prompt chain instead. Performance trade-offs?",
                "The architecture makes sense but latency on the webhook side could be the bottleneck.",
                "Schema validation is where most automations break. How are you handling unstructured inputs?",
            ]
            comment_text = random.choice(builder_comments)

        elif name == "tech_peer_critic":
            critic_comments = [
                "The approach is sound but the claim about 95% accuracy needs methodological rigor. How was that measured?",
                "Survivorship bias here — you're showing the wins. What's the failure rate in production?",
                "Correlation between adoption and outcome isn't shown. This could be correlation, not causation.",
                "The methodology assumes stable input distributions. Real production data is messier than labeled test sets.",
            ]
            comment_text = random.choice(critic_comments)

        elif name == "contrarian_veteran":
            contrarian_comments = [
                "Everyone's building this, but adoption is the real problem. You're solving a supply problem, not a demand problem.",
                "This is good, but the real constraint for Indian SMBs isn't tools — it's capital and talent retention.",
                "Bold vision, but most founders underestimate tribal knowledge and customer relationship costs.",
                "The shift isn't technical; it's organizational. Tools enable, culture decides.",
            ]
            comment_text = random.choice(contrarian_comments)

        elif name == "contrarian_academic":
            academic_comments = [
                "Interesting approach, but where's the empirical evidence? Have you conducted a randomized controlled trial?",
                "The assumptions need validation against real-world data, not synthetic benchmarks.",
                "This aligns with recent research on automation ROI, but generalizability across domains is limited.",
                "Good case study, but statistical significance requires larger sample sizes and control groups.",
            ]
            comment_text = random.choice(academic_comments)

        elif name == "aspiring_smb_eager":
            eager_comments = [
                "This is exactly what we need! Can this work in Hindi? Our team speaks mostly Hindi.",
                "How much does this cost per month? Is there a demo or trial?",
                "Does this integrate with our existing WhatsApp Business account?",
                "What's the training time? Can our staff learn this, or do we need an engineer?",
            ]
            comment_text = random.choice(eager_comments)

        elif name == "aspiring_smb_cautious":
            cautious_comments = [
                "Interesting, but what's the total cost including setup, training, and support?",
                "How long before we see ROI? We need numbers before committing.",
                "Is there vendor lock-in? What if we want to switch platforms later?",
                "What happens if something breaks? What's the support model?",
            ]
            comment_text = random.choice(cautious_comments)

        elif name == "lurker_passive":
            # Lurkers almost never comment
            comment_text = None

    # Apply stochastic probability: take action only if probability draw succeeds
    if not _maybe(prob):
        # Fallback: downgrade action to a lower-engagement level
        if action in ("SAVE", "SHARE"):
            action = "LIKE"
        elif action in ("COMMENT", "LIKE"):
            action = "READ"
        elif action == "READ":
            action = "SKIM"
        elif action == "SKIM":
            action = "SKIP"
        comment_text = None  # Remove comment if action downgraded
        dwell = max(2, dwell // 2)  # Reduce dwell time

    reasoning = f"{persona['display']}: {'stops for' if action != 'SKIP' else 'skips'} — {persona['stops_for'] if action != 'SKIP' else persona['skip_threshold']}"

    return PersonaReaction(
        persona_name=name,
        action=action,
        probability=prob,
        reasoning=reasoning,
        comment_text=comment_text,
        dwell_seconds=dwell,
    )


def simulate_thread_heuristic(reactions: list[PersonaReaction]) -> list[ThreadReply]:
    """Simulate comment thread replies using heuristics."""
    replies = []
    commenters = [r for r in reactions if r.action == "COMMENT" and r.comment_text]

    if len(commenters) < 2:
        return replies

    # Round 1: First commenter triggers response from contrarians
    for i, commenter in enumerate(commenters):
        for j, other in enumerate(commenters):
            if i != j and "contrarian" in other.persona_name and "contrarian" not in commenter.persona_name:
                replies.append(ThreadReply(
                    author=other.persona_name,
                    replying_to=commenter.persona_name,
                    text=f"@{commenter.persona_name.split('_')[0]} I see your point, but the data suggests a more nuanced picture. The 60-70% AI ratio works in Western markets — Indian SMBs may need different ratios given cultural expectations around personal service.",
                    round_num=1,
                ))

    # Round 2: Original commenter responds
    for reply in list(replies):
        original = next((c for c in commenters if c.persona_name == reply.replying_to), None)
        if original and "tech" in original.persona_name:
            replies.append(ThreadReply(
                author=original.persona_name,
                replying_to=reply.author,
                text=f"Fair point on the ratio — our Bangalore deployment actually started at 40% AI and scaled to 70% over 3 months as the system learned. The ramp-up period is what most posts miss.",
                round_num=2,
            ))

    return replies


# ─── API-Based Simulation (Provider-Agnostic) ───

def _build_persona_prompt(persona: dict, post_text: str, post_format: str) -> str:
    """Build the prompt for LLM-based persona simulation."""
    return f"""You are {persona['display']}, a LinkedIn user with this profile:
- Role: {persona['role']}
- Scroll speed: {persona['scroll_speed']}
- Stops for: {persona['stops_for']}
- Comment style: {persona['comment_style']}
- Saves when: {persona['save_threshold']}
- Skips when: {persona['skip_threshold']}

You are scrolling LinkedIn. You see this {post_format} post:
---
{post_text}
---

Based on your profile, decide your action. Respond ONLY in this exact JSON format:
{{"action": "SKIP|SKIM|READ|LIKE|COMMENT|SAVE|SHARE", "probability": 0-100, "dwell_seconds": N, "reasoning": "one sentence", "comment_text": "if action is COMMENT, write your actual comment in character, otherwise null"}}"""


def api_simulate_persona(llm_client, persona: dict, post_text: str, post_format: str) -> PersonaReaction:
    """Use LLM API to simulate a persona reaction."""
    prompt = _build_persona_prompt(persona, post_text, post_format)

    try:
        text = llm_client.complete("fast", prompt, max_tokens=300)
        if text:
            json_match = re.search(r'\{[^{}]+\}', text, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
                return PersonaReaction(
                    persona_name=persona["name"],
                    action=data.get("action", "SKIP"),
                    probability=data.get("probability", 50),
                    reasoning=data.get("reasoning", ""),
                    comment_text=data.get("comment_text"),
                    dwell_seconds=data.get("dwell_seconds", 5),
                )
    except Exception as e:
        print(f"  API error for {persona['name']}: {e}")

    # Fallback to heuristic
    return heuristic_simulate_persona(persona, post_text, post_format)


# ─── Simulation Engine ───

class SimulationEngine:
    def __init__(self, disable_api: bool = False):
        self.root = get_postforge_root()
        self.personas = load_personas()
        self.api_available = False
        self.llm = None

        # Initialize provider-agnostic LLM client
        if not disable_api:
            try:
                from llm_client import LLMClient
                self.llm = LLMClient()
                self.api_available = self.llm.available
            except ImportError:
                pass

    def simulate_variant(self, variant_path: str) -> VariantSimulation:
        """Run full simulation on a single variant."""
        path = Path(variant_path)
        if not path.exists():
            raise FileNotFoundError(f"Variant not found: {variant_path}")

        content = load_md(path)

        # Extract post text and metadata
        post_text = ""
        post_format = "text"
        variant_id = path.stem.replace("variant_", "").upper()

        in_post = False
        for line in content.split("\n"):
            if line.startswith("## Post Text"):
                in_post = True
                continue
            elif line.startswith("## ") and in_post:
                in_post = False
            elif in_post:
                post_text += line + "\n"

            if line.startswith("- Format:"):
                post_format = line.split(":", 1)[1].strip().lower()

        post_text = post_text.strip()
        if not post_text:
            # Fallback: use everything between metadata and first comment
            lines = content.split("\n")
            capture = False
            for line in lines:
                if line.startswith("## Post Text"):
                    capture = True
                    continue
                if capture and line.startswith("## "):
                    break
                if capture:
                    post_text += line + "\n"
            post_text = post_text.strip()

        if not post_text:
            post_text = content  # Last resort: use full file

        print(f"\n  Simulating Variant {variant_id} ({post_format})")
        print(f"  Personas: {len(self.personas)}")
        mode_label = f"API ({self.llm.provider_name})" if self.api_available and self.llm else "Heuristic"
        print(f"  Mode: {mode_label}")

        # Phase 1: Initial reactions
        reactions = []
        if self.api_available:
            reactions = self._api_simulate_all_sync(post_text, post_format)
        else:
            for persona in self.personas:
                reaction = heuristic_simulate_persona(persona, post_text, post_format)
                reactions.append(reaction)

        # Phase 2: Thread simulation
        thread_replies = simulate_thread_heuristic(reactions)

        # Phase 3: Aggregate metrics
        metrics = self._aggregate_metrics(reactions, thread_replies)

        # Build result
        sim = VariantSimulation(
            variant_id=variant_id,
            reactions=reactions,
            thread_replies=thread_replies,
            metrics=metrics,
        )

        # Top comments
        sim.top_comments = [r.comment_text for r in reactions if r.comment_text][:5]

        # Thread preview
        if thread_replies:
            first = thread_replies[0]
            sim.thread_preview = f"{first.author}: '{first.text[:80]}...' → replied to {first.replying_to}"

        # Print summary
        print(f"  Results:")
        print(f"    Comments: {metrics.comment_count} | Saves: {metrics.save_count} | Likes: {metrics.like_count}")
        print(f"    Avg dwell: {metrics.avg_dwell_seconds:.0f}s | Thread depth: {metrics.avg_thread_depth:.1f}")
        print(f"    Debate heat: {metrics.debate_heat_score:.2f} | Engagement: {metrics.engagement_rate:.1f}%")

        return sim

    def _api_simulate_all_sync(self, post_text: str, post_format: str) -> list[PersonaReaction]:
        """Run all persona simulations via LLM API sequentially."""
        return [
            api_simulate_persona(self.llm, persona, post_text, post_format)
            for persona in self.personas
        ]

    def _aggregate_metrics(self, reactions: list[PersonaReaction], threads: list[ThreadReply]) -> SimulatedMetrics:
        """Calculate aggregate metrics from reactions and threads."""
        comment_count = sum(1 for r in reactions if r.action == "COMMENT")
        save_count = sum(1 for r in reactions if r.action == "SAVE")
        like_count = sum(1 for r in reactions if r.action == "LIKE")
        share_count = sum(1 for r in reactions if r.action == "SHARE")

        dwell_times = [r.dwell_seconds for r in reactions if r.dwell_seconds > 0]
        avg_dwell = sum(dwell_times) / max(len(dwell_times), 1)

        # Thread depth
        max_round = max((t.round_num for t in threads), default=0)
        avg_thread_depth = (comment_count + len(threads)) / max(comment_count, 1) if comment_count > 0 else 0

        # Engagement rate (simulated: total actions / total personas)
        total_engaged = sum(1 for r in reactions if r.action not in ("SKIP",))
        engagement_rate = total_engaged / max(len(reactions), 1) * 100

        # Debate heat: thread replies × variety of commenters
        unique_thread_authors = len(set(t.author for t in threads))
        debate_heat = len(threads) * (unique_thread_authors / max(len(self.personas), 1))

        return SimulatedMetrics(
            engagement_rate=round(engagement_rate, 1),
            comment_count=comment_count,
            avg_thread_depth=round(avg_thread_depth, 1),
            save_count=save_count,
            share_count=share_count,
            like_count=like_count,
            avg_dwell_seconds=round(avg_dwell, 1),
            debate_heat_score=round(debate_heat, 2),
        )

    def simulate_all_variants(self, date: str) -> dict[str, VariantSimulation]:
        """Simulate all 6 variants for a given date."""
        variants_dir = self.root / "output" / "variants" / date
        if not variants_dir.exists():
            raise FileNotFoundError(f"No variants found for {date}")

        results = {}
        for variant_file in sorted(variants_dir.glob("variant_*.md")):
            sim = self.simulate_variant(str(variant_file))
            results[sim.variant_id] = sim

        return results

    def rank_variants(self, results: dict[str, VariantSimulation]) -> list[tuple[str, float]]:
        """Rank variants by composite score."""
        if not results:
            return []

        # Normalize metrics across variants
        max_saves = max(r.metrics.save_count for r in results.values()) or 1
        max_comments = max(r.metrics.comment_count for r in results.values()) or 1
        max_depth = max(r.metrics.avg_thread_depth for r in results.values()) or 1

        for vid, sim in results.items():
            sim.composite_score = (
                0.40 * (sim.metrics.save_count / max_saves) +
                0.35 * (sim.metrics.comment_count / max_comments) +
                0.25 * (sim.metrics.avg_thread_depth / max_depth)
            )

        ranked = sorted(results.items(), key=lambda x: x[1].composite_score, reverse=True)
        return [(vid, sim.composite_score) for vid, sim in ranked]

    def save_results(self, results: dict[str, VariantSimulation], date: str, suffix: str = ""):
        """Save simulation results to JSON."""
        filename = f"{date}{suffix}.json"
        output_path = self.root / "output" / "simulations" / filename

        output = {
            "date": date,
            "simulated_at": datetime.now().isoformat(),
            "mode": "api" if self.api_available else "heuristic",
            "personas_used": len(self.personas),
            "rounds": 2,
            "variants": {},
        }

        rankings = self.rank_variants(results)

        for vid, sim in results.items():
            output["variants"][vid] = {
                "simulated_engagement_rate": sim.metrics.engagement_rate,
                "comment_count": sim.metrics.comment_count,
                "avg_thread_depth": sim.metrics.avg_thread_depth,
                "save_count": sim.metrics.save_count,
                "like_count": sim.metrics.like_count,
                "share_count": sim.metrics.share_count,
                "avg_dwell_seconds": sim.metrics.avg_dwell_seconds,
                "debate_heat": sim.metrics.debate_heat_score,
                "composite_score": round(sim.composite_score, 3),
                "top_comments": sim.top_comments,
                "thread_preview": sim.thread_preview,
                "reactions": [
                    {
                        "persona": r.persona_name,
                        "action": r.action,
                        "probability": r.probability,
                        "dwell_seconds": r.dwell_seconds,
                        "comment_text": r.comment_text,
                    } for r in sim.reactions
                ],
            }

        if rankings:
            output["winner"] = rankings[0][0]
            output["ranking"] = [{"variant": v, "composite": round(s, 3)} for v, s in rankings]

        save_json(output_path, output)
        print(f"\n  Saved to {output_path}")
        return output_path


# ─── CLI Entry ───

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python scripts/simulator.py <variant_path>       # simulate one variant")
        print("  python scripts/simulator.py --all <date>          # simulate all variants for date")
        sys.exit(0)

    engine = SimulationEngine()

    if sys.argv[1] == "--all":
        date = sys.argv[2] if len(sys.argv) > 2 else get_today()
        results = engine.simulate_all_variants(date)
        rankings = engine.rank_variants(results)

        print("\n  ─── SIMULATION RANKING ───")
        for i, (vid, score) in enumerate(rankings):
            sim = results[vid]
            print(f"  #{i+1} Variant {vid}: composite={score:.3f} "
                  f"(saves={sim.metrics.save_count}, comments={sim.metrics.comment_count}, "
                  f"depth={sim.metrics.avg_thread_depth:.1f})")

        print(f"\n  WINNER: Variant {rankings[0][0]}")
        engine.save_results(results, date)

    else:
        variant_path = sys.argv[1]
        sim = engine.simulate_variant(variant_path)
        engine.save_results({sim.variant_id: sim}, get_today(), f"-variant_{sim.variant_id.lower()}")
