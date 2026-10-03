"""Checks for the repository's own maintenance setup."""

from .constants import AUTHORING_PLUGIN
from .model import Context, Status


def check_maintenance_setup(ctx: Context) -> None:
    check = "maintenance setup"
    with ctx.reporter.failures_as(check, OSError, ValueError):
        if (ctx.root / "CLAUDE.md").read_text().strip() != "@AGENTS.md":
            raise ValueError("CLAUDE.md must import shared instructions")
        if not (ctx.root / "AGENTS.md").is_file():
            raise ValueError("missing AGENTS.md")
        settings = ctx.load_json(ctx.root / ".claude/settings.json")
        if settings is None or settings.get("enabledPlugins", {}).get(AUTHORING_PLUGIN) is not True:
            raise ValueError("project must enable upstream plugin-dev")
        ctx.reporter.record(Status.PASS, check, "shared instructions and Claude authoring dependency")
