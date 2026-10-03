"""Cross-catalog and cross-manifest consistency checks."""

from .catalogs import Registry
from .constants import CLAUDE, CODEX, SHARED_MANIFEST_FIELDS
from .model import Context, Status


def check_marketplace_identity(ctx: Context, registry: Registry) -> None:
    catalogs = registry.catalogs
    if len(catalogs) == 2 and catalogs[CODEX].get("name") != catalogs[CLAUDE].get("name"):
        ctx.reporter.record(Status.FAILED, "marketplace identity", "catalog names differ")


def check_metadata_drift(ctx: Context, registry: Registry) -> None:
    for name, manifests in registry.manifests.items():
        first, *others = manifests
        for field in SHARED_MANIFEST_FIELDS:
            if any(other.get(field) != first.get(field) for other in others):
                ctx.reporter.record(Status.FAILED, f"metadata {name}", f"{field} differs between manifests")


def check_catalog_membership(ctx: Context, registry: Registry) -> None:
    plugins_dir = ctx.root / "plugins"
    if not plugins_dir.exists():
        return
    for plugin in plugins_dir.iterdir():
        if plugin.is_dir() and plugin.name not in registry.bundles:
            ctx.reporter.record(Status.FAILED, "catalog membership", f"uncataloged plugin: {plugin.name}")
