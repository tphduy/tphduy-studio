"""The Verifier facade that runs every check in order."""

from pathlib import Path

from .bundles import check_bundles
from .catalogs import check_catalogs
from .consistency import check_catalog_membership, check_marketplace_identity, check_metadata_drift
from .maintenance import check_maintenance_setup
from .markdown import check_markdown
from .model import Context, Reporter
from .native import check_native


class Verifier:
    def __init__(self, root):
        self.root = Path(root).resolve()
        self.reporter = Reporter()
        self.context = Context(self.root, self.reporter)

    @property
    def results(self) -> list[dict]:
        return self.reporter.results

    def structure(self) -> None:
        registry = check_catalogs(self.context)
        check_marketplace_identity(self.context, registry)
        check_metadata_drift(self.context, registry)
        check_catalog_membership(self.context, registry)
        check_bundles(self.context, registry.bundles)
        check_markdown(self.context, registry.bundles)
        check_maintenance_setup(self.context)

    def native(self, skip: bool = False) -> None:
        check_native(self.context, skip)

    def report(self) -> dict:
        return {"status": self.reporter.overall(), "checks": self.results}
