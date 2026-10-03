"""Path containment rules for catalog and manifest references."""

from pathlib import Path


def resolve_contained(base: Path, value, check: str) -> Path:
    """Resolve a `./`-prefixed reference under `base`, raising ValueError when malformed, escaping or missing."""
    if not isinstance(value, str) or not value.startswith("./"):
        raise ValueError(f"{check}: expected a ./-prefixed path")
    path = (base / value).resolve()
    if not path.is_relative_to(base.resolve()):
        raise ValueError(f"{check}: path escapes its root: {value}")
    if not path.exists():
        raise ValueError(f"{check}: missing path: {value}")
    return path
