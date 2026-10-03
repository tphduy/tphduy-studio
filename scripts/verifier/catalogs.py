"""Marketplace catalog checks that also discover the plugin bundles they list."""

from dataclasses import dataclass, field
from pathlib import Path

from .constants import AUTHENTICATION_POLICIES, CATALOGS, CLAUDE, CODEX, INSTALLATION_POLICIES, MAX_NAME_LENGTH, NAME
from .manifests import check_manifest
from .model import Context, Status
from .paths import resolve_contained


@dataclass
class Registry:
    """Plugins discovered so far, kept even when a later catalog entry fails."""

    catalogs: dict[str, dict] = field(default_factory=dict)
    bundles: dict[str, Path] = field(default_factory=dict)
    manifests: dict[str, list[dict]] = field(default_factory=dict)


def validate_catalog_header(catalog: dict, platform: str) -> None:
    if not NAME.fullmatch(str(catalog.get("name", ""))):
        raise ValueError("invalid marketplace name")
    if platform == CLAUDE and not catalog.get("owner", {}).get("name"):
        raise ValueError("missing owner.name")
    if not isinstance(catalog.get("plugins"), list):
        raise ValueError("plugins must be an array")


def validate_entry_name(entry: dict, seen: set[str]) -> str:
    name = entry.get("name", "")
    if not isinstance(name, str) or not NAME.fullmatch(name) or len(name) > MAX_NAME_LENGTH:
        raise ValueError("invalid plugin name")
    if name in seen:
        raise ValueError(f"duplicate plugin: {name}")
    seen.add(name)
    if "version" in entry:
        raise ValueError(f"{name}: keep version in the manifest only")
    return name


def codex_source_path(entry: dict, name: str):
    """Validate the Codex-only entry fields and return the plugin source path."""
    source = entry.get("source")
    if not isinstance(source, dict) or source.get("source") != "local":
        raise ValueError(f"{name}: this repository expects local directory sources")
    policy = entry.get("policy", {})
    if policy.get("installation") not in INSTALLATION_POLICIES:
        raise ValueError(f"{name}: invalid installation policy")
    if policy.get("authentication") not in AUTHENTICATION_POLICIES:
        raise ValueError(f"{name}: invalid authentication policy")
    if not isinstance(entry.get("category"), str) or not entry["category"].strip():
        raise ValueError(f"{name}: missing category")
    return source.get("path")


def plugin_directory(ctx: Context, name: str, source) -> Path:
    plugin = resolve_contained(ctx.root, source, name)
    if plugin != ctx.root / "plugins" / name or not plugin.is_dir():
        raise ValueError(f"{name}: expected plugins/{name}/")
    return plugin


def register_entry(ctx: Context, platform: str, entry, seen: set[str], registry: Registry) -> None:
    if not isinstance(entry, dict):
        raise ValueError("plugin entry must be an object")
    name = validate_entry_name(entry, seen)
    source = codex_source_path(entry, name) if platform == CODEX else entry.get("source")
    plugin = plugin_directory(ctx, name, source)
    registry.bundles[name] = plugin
    manifest = check_manifest(ctx, plugin, platform, name)
    if manifest is not None:
        registry.manifests.setdefault(name, []).append(manifest)


def check_catalog(ctx: Context, platform: str, registry: Registry) -> None:
    catalog = ctx.load_json(ctx.root / CATALOGS[platform])
    if catalog is None:
        return
    registry.catalogs[platform] = catalog
    seen: set[str] = set()
    with ctx.reporter.failures_as(f"{platform} catalog", ValueError, TypeError, AttributeError):
        validate_catalog_header(catalog, platform)
        for entry in catalog["plugins"]:
            register_entry(ctx, platform, entry, seen, registry)
        ctx.reporter.record(Status.PASS, f"{platform} catalog", f"{len(seen)} plugin(s)")


def check_catalogs(ctx: Context) -> Registry:
    registry = Registry()
    for platform in CATALOGS:
        check_catalog(ctx, platform, registry)
    return registry
