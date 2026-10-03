"""Local link checks for Markdown files in the repository and its plugin bundles."""

from pathlib import Path
from urllib.parse import unquote, urlsplit

from .constants import MARKDOWN_LINK
from .model import Context, Status


def parse_target(raw: str) -> str:
    target = raw.strip()
    if target.startswith("<"):
        return target[1:target.find(">")]
    return target.split()[0] if target else ""


def local_links(text: str):
    """Yield `(target, path)` for every link that points at a local file."""
    for raw in MARKDOWN_LINK.findall(text):
        target = parse_target(raw)
        url = urlsplit(target)
        if not (url.scheme or url.netloc or not url.path):
            yield target, unquote(url.path)


def check_links(path: Path, base: Path) -> None:
    if not path.resolve().is_relative_to(base):
        raise ValueError("Markdown file escapes its root")
    for target, relative in local_links(path.read_text()):
        destination = (path.parent / relative).resolve()
        if not destination.is_relative_to(base) or not destination.exists():
            raise ValueError(f"missing or escaping local link: {target}")


def markdown_files(root: Path, bundles: dict[str, Path]) -> list[Path]:
    files = list(root.glob("*.md")) + list((root / "docs").rglob("*.md"))
    for plugin in bundles.values():
        files.extend(plugin.rglob("*.md"))
    return files


def check_markdown(ctx: Context, bundles: dict[str, Path]) -> None:
    files = markdown_files(ctx.root, bundles)
    for path in files:
        base = next((plugin for plugin in bundles.values() if path.is_relative_to(plugin)), ctx.root)
        with ctx.reporter.failures_as(ctx.relative(path), OSError, ValueError):
            check_links(path, base)
    ctx.reporter.record(Status.PASS, "Markdown scan", f"scanned {len(files)} file(s); link failures reported separately")
