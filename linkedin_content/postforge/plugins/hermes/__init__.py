"""PostForge plugin — registration."""

import logging

from . import schemas, tools

logger = logging.getLogger(__name__)


def _on_post_tool_call(tool_name, args, result, task_id, **kwargs):
    """Log PostForge tool calls for debugging."""
    if tool_name.startswith("postforge_"):
        logger.info("PostForge tool called: %s (session %s)", tool_name, task_id)


def register(ctx):
    """Wire PostForge tools and hooks into Hermes."""
    ctx.register_tool(
        name="postforge_status",
        toolset="postforge",
        schema=schemas.POSTFORGE_STATUS,
        handler=tools.postforge_status,
        description="PostForge system health dashboard",
        emoji="📊",
    )
    ctx.register_tool(
        name="postforge_generate",
        toolset="postforge",
        schema=schemas.POSTFORGE_GENERATE,
        handler=tools.postforge_generate,
        description="Generate LinkedIn post variants",
        emoji="✍️",
    )
    ctx.register_tool(
        name="postforge_simulate",
        toolset="postforge",
        schema=schemas.POSTFORGE_SIMULATE,
        handler=tools.postforge_simulate,
        description="Run audience persona simulation",
        emoji="🎭",
    )
    ctx.register_tool(
        name="postforge_learn",
        toolset="postforge",
        schema=schemas.POSTFORGE_LEARN,
        handler=tools.postforge_learn,
        description="Input post metrics for learning",
        emoji="📈",
    )
    ctx.register_tool(
        name="postforge_sprint_review",
        toolset="postforge",
        schema=schemas.POSTFORGE_SPRINT_REVIEW,
        handler=tools.postforge_sprint_review,
        description="Sprint review and weight recalibration",
        emoji="🔄",
    )
    ctx.register_tool(
        name="postforge_scores",
        toolset="postforge",
        schema=schemas.POSTFORGE_SCORES,
        handler=tools.postforge_scores,
        description="Read variant scoring results",
        emoji="🏆",
    )
    ctx.register_tool(
        name="postforge_read_variant",
        toolset="postforge",
        schema=schemas.POSTFORGE_READ_VARIANT,
        handler=tools.postforge_read_variant,
        description="Read a specific post variant",
        emoji="📄",
    )

    ctx.register_hook("post_tool_call", _on_post_tool_call)

    logger.info("PostForge plugin registered: 7 tools, 1 hook")
