"""Per-plugin bundle scan: path containment, stray JSON files, and skills."""

from pathlib import Path

from .model import Context, Status
from .skills import check_skills


def check_bundle_files(ctx: Context, name: str, plugin: Path) -> None:
    for path in plugin.rglob("*"):
        if not path.resolve().is_relative_to(plugin):
            ctx.reporter.record(Status.FAILED, f"bundle {name}", f"path escapes plugin: {path.name}")
        elif path.is_file() and path.suffix == ".json" and path.name != "plugin.json":
            ctx.load_json(path)


def check_bundles(ctx: Context, bundles: dict[str, Path]) -> None:
    for name, plugin in bundles.items():
        check_bundle_files(ctx, name, plugin)
        check_skills(ctx, name, plugin)
