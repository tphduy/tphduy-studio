"""Plugin manifest checks for both platforms."""

from pathlib import Path

from .constants import CODEX, MANIFESTS, PORTABLE_FORBIDDEN_KEYS, PORTABLE_SCHEMA, VERSION
from .model import Context, Status
from .paths import resolve_contained


def iter_path_references(value):
    """Yield every `./`-prefixed string nested anywhere inside a manifest value."""
    if isinstance(value, dict):
        for child in value.values():
            yield from iter_path_references(child)
    elif isinstance(value, list):
        for child in value:
            yield from iter_path_references(child)
    elif isinstance(value, str) and value.startswith("./"):
        yield value


def validate_common_fields(data: dict, name: str) -> None:
    if data.get("name") != name:
        raise ValueError("catalog and manifest names differ")
    if not VERSION.fullmatch(str(data.get("version", ""))):
        raise ValueError("expected a semantic version")
    if not isinstance(data.get("description"), str) or not data["description"].strip():
        raise ValueError("missing description")
    if not isinstance(data.get("author"), dict) or not data["author"].get("name"):
        raise ValueError("missing author.name")


def validate_portable_fields(data: dict) -> None:
    if data.get("$schema") != PORTABLE_SCHEMA:
        raise ValueError("expected the portable Agent Plugins schema")
    if any(key in data for key in PORTABLE_FORBIDDEN_KEYS):
        raise ValueError("portable components use fixed paths or extensions.com.openai")


def validate_manifest(data: dict, platform: str, name: str, plugin: Path) -> None:
    validate_common_fields(data, name)
    if platform == CODEX:
        validate_portable_fields(data)
    for reference in iter_path_references(data):
        resolve_contained(plugin, reference, "manifest reference")


def check_manifest(ctx: Context, plugin: Path, platform: str, name: str) -> dict | None:
    """Validate one plugin manifest, returning its data when it could be loaded."""
    data = ctx.load_json(plugin / MANIFESTS[platform])
    if data is None:
        return None
    check = f"{platform} manifest {name}"
    with ctx.reporter.failures_as(check, ValueError):
        validate_manifest(data, platform, name, plugin)
        ctx.reporter.record(Status.PASS, check, data["version"])
    return data
