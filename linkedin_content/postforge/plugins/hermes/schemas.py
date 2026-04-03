"""PostForge tool schemas — what the LLM sees."""

POSTFORGE_STATUS = {
    "name": "postforge_status",
    "description": (
        "Check PostForge system health. Shows scoring weights version, "
        "calibration post count, performance history, sprint status, and "
        "today's content pipeline state. Use this to understand the current "
        "state of the LinkedIn content engine before taking action."
    ),
    "parameters": {
        "type": "object",
        "properties": {},
        "required": [],
    },
}

POSTFORGE_GENERATE = {
    "name": "postforge_generate",
    "description": (
        "Generate LinkedIn post variants using the PostForge content pipeline. "
        "Runs intake, research, writing (6 variants), scoring, and simulation. "
        "Use when the user wants to create new LinkedIn content. "
        "Returns ranked variants with scores and predictions."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "topic": {
                "type": "string",
                "description": "The topic for the LinkedIn post (e.g., 'AI agents replacing SaaS for Indian SMBs')",
            },
            "goal": {
                "type": "string",
                "enum": ["saves", "comments", "impressions"],
                "description": "Optimization goal: 'saves' for reference content, 'comments' for engagement, 'impressions' for reach",
            },
            "force": {
                "type": "boolean",
                "description": "Force re-generation even if variants already exist for today (default: false)",
            },
            "auto_select": {
                "type": "boolean",
                "description": "Automatically select the top-ranked variant (default: false)",
            },
        },
        "required": ["topic"],
    },
}

POSTFORGE_SIMULATE = {
    "name": "postforge_simulate",
    "description": (
        "Run multi-agent audience simulation on post variants. "
        "10 personas react to each variant with stochastic behavior — "
        "likes, comments, saves, shares, or scroll-past. "
        "Use to preview how different audience segments would respond "
        "to content before publishing."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "target": {
                "type": "string",
                "description": (
                    "What to simulate. Either a date (YYYY-MM-DD) to simulate all "
                    "variants for that day, or a path to a specific variant markdown file."
                ),
            },
        },
        "required": ["target"],
    },
}

POSTFORGE_LEARN = {
    "name": "postforge_learn",
    "description": (
        "Input actual LinkedIn post metrics for a published variant. "
        "Records impressions, likes, comments, saves, shares, and engagement data. "
        "Use after a post has been live for 24 hours and again at 7 days. "
        "This data feeds the self-improvement loop."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "post_id": {
                "type": "string",
                "description": "Post identifier in YYYY-MM-DD-X format (e.g., '2026-04-03-A' for variant A on April 3rd)",
            },
            "impressions": {
                "type": "integer",
                "description": "Total impression count from LinkedIn analytics",
            },
            "likes": {
                "type": "integer",
                "description": "Total like/reaction count",
            },
            "comments": {
                "type": "integer",
                "description": "Total comment count",
            },
            "saves": {
                "type": "integer",
                "description": "Total save/bookmark count",
            },
            "shares": {
                "type": "integer",
                "description": "Total repost/share count",
            },
            "profile_visits": {
                "type": "integer",
                "description": "Profile visits attributed to the post (optional, default 0)",
            },
        },
        "required": ["post_id", "impressions", "likes", "comments", "saves", "shares"],
    },
}

POSTFORGE_SPRINT_REVIEW = {
    "name": "postforge_sprint_review",
    "description": (
        "Run a sprint review analysis. Compares predicted scores vs actual metrics, "
        "recalibrates scoring weights via EMA, and extracts winning hooks and anti-patterns. "
        "Should be run every 3 days after enough posts have metrics. "
        "Returns weight changes and performance insights."
    ),
    "parameters": {
        "type": "object",
        "properties": {},
        "required": [],
    },
}

POSTFORGE_SCORES = {
    "name": "postforge_scores",
    "description": (
        "Read scoring results for a specific date's variants. "
        "Returns per-variant scores across 6 dimensions (hook, saves, comments, "
        "dwell, voice, compliance), composite scores, and ranking. "
        "Use to review how variants compared before simulation."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "date": {
                "type": "string",
                "description": "Date to read scores for in YYYY-MM-DD format (defaults to today)",
            },
        },
        "required": [],
    },
}

POSTFORGE_READ_VARIANT = {
    "name": "postforge_read_variant",
    "description": (
        "Read the full text of a specific post variant. "
        "Use to review what a variant actually says before publishing, simulating, or comparing."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "date": {
                "type": "string",
                "description": "Date in YYYY-MM-DD format (defaults to today)",
            },
            "variant": {
                "type": "string",
                "enum": ["a", "b", "c", "d", "e", "f"],
                "description": "Variant letter (a through f)",
            },
        },
        "required": ["variant"],
    },
}
