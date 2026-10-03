"""Skill directory layout and SKILL.md frontmatter checks."""

from pathlib import Path

import yaml

from .constants import MAX_NAME_LENGTH, NAME
from .loading import read_frontmatter
from .model import Context, Status


def validate_frontmatter(data, directory_name: str) -> None:
    if not isinstance(data, dict) or data.get("name") != directory_name:
        raise ValueError("skill name must match its directory")
    if not NAME.fullmatch(data["name"]) or len(data["name"]) > MAX_NAME_LENGTH:
        raise ValueError("invalid skill name")
    if not isinstance(data.get("description"), str) or not data["description"].strip():
        raise ValueError("missing skill description")


def check_skill(ctx: Context, plugin_name: str, plugin: Path, skill: Path) -> None:
    check = f"skill {plugin_name}/{skill.parent.name}"
    with ctx.reporter.failures_as(check, OSError, ValueError, yaml.YAMLError):
        if not skill.resolve().is_relative_to(plugin):
            raise ValueError("skill path escapes plugin")
        validate_frontmatter(read_frontmatter(skill.read_text()), skill.parent.name)
        ctx.reporter.record(Status.PASS, check, "valid frontmatter")


def check_skills(ctx: Context, plugin_name: str, plugin: Path) -> None:
    skills_dir = plugin / "skills"
    if skills_dir.exists() and not skills_dir.is_dir():
        ctx.reporter.record(Status.FAILED, f"bundle {plugin_name}", "skills must be a directory")
        return
    for directory in skills_dir.glob("*"):
        if directory.is_dir() and not directory.name.startswith(".") and not (directory / "SKILL.md").is_file():
            ctx.reporter.record(Status.FAILED, f"skill {plugin_name}/{directory.name}", "missing SKILL.md")
    for skill in skills_dir.glob("*/SKILL.md"):
        check_skill(ctx, plugin_name, plugin, skill)
