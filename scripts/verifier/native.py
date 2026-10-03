"""Run Claude's native plugin validator and interpret its JSON report."""

import json
from pathlib import Path
import shutil
import subprocess

from .constants import CATALOGS, CLAUDE, NAME, NATIVE_TIMEOUT_SECONDS
from .model import Context, Status

UNEXPECTED_ERROR_EXIT = 2


def validation_targets(ctx: Context) -> list[Path]:
    catalog_path = ctx.root / CATALOGS[CLAUDE]
    targets = [catalog_path]
    catalog = ctx.load_json(catalog_path)
    if catalog is not None and isinstance(catalog.get("plugins"), list):
        targets.extend(
            ctx.root / "plugins" / entry["name"]
            for entry in catalog["plugins"]
            if isinstance(entry, dict) and isinstance(entry.get("name"), str) and NAME.fullmatch(entry["name"])
        )
    return targets


def report_problems(report: dict) -> list:
    problems = [*report["manifest"]["errors"], *report["manifest"]["warnings"]]
    for item in report.get("contents", []):
        problems += [*item.get("errors", []), *item.get("warnings", [])]
    return problems


def validate_target(ctx: Context, target: Path) -> None:
    check = f"Claude validate {ctx.relative(target)}"
    try:
        process = subprocess.run(["claude", "plugin", "validate", str(target), "--strict", "--json"], capture_output=True, text=True, timeout=NATIVE_TIMEOUT_SECONDS)
    except (OSError, subprocess.TimeoutExpired) as error:
        ctx.reporter.record(Status.INCONCLUSIVE, "Claude native validation", error)
        return
    if process.returncode == UNEXPECTED_ERROR_EXIT:
        ctx.reporter.record(Status.INCONCLUSIVE, check, f"validator hit an unexpected error: {process.stderr.strip()}")
        return
    try:
        report = json.loads(process.stdout)
        problems = report_problems(report)
        passed = report["success"] is True and process.returncode == 0 and not problems
    except (ValueError, KeyError, TypeError, AttributeError) as error:
        ctx.reporter.record(Status.FAILED, check, f"unreadable validator JSON: {error}")
        return
    if passed:
        ctx.reporter.record(Status.PASS, check, "success: true, no errors or warnings")
    else:
        ctx.reporter.record(Status.FAILED, check, f"exit {process.returncode}: {problems or process.stdout.strip()}")


def check_native(ctx: Context, skip: bool = False) -> None:
    if skip or not shutil.which("claude"):
        ctx.reporter.record(Status.INCONCLUSIVE, "Claude native validation", "skipped" if skip else "claude is not installed")
        return
    for target in validation_targets(ctx):
        validate_target(ctx, target)
