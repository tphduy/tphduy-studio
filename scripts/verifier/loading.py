"""Strict JSON and YAML readers that reject duplicate keys."""

import json
from pathlib import Path

import yaml

from .constants import FRONTMATTER


def unique_pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate key: {key}")
        result[key] = value
    return result


class UniqueLoader(yaml.SafeLoader):
    pass


def _yaml_mapping(loader, node):
    loader.flatten_mapping(node)
    return unique_pairs((loader.construct_object(k), loader.construct_object(v)) for k, v in node.value)


UniqueLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _yaml_mapping)


def read_json_object(path: Path) -> dict:
    """Return the JSON object stored at `path`, raising OSError or ValueError when unreadable."""
    value = json.loads(path.read_text(), object_pairs_hook=unique_pairs)
    if not isinstance(value, dict):
        raise ValueError("expected a JSON object")
    return value


def read_frontmatter(text: str):
    """Return the parsed YAML frontmatter of a Markdown document, raising ValueError or YAMLError when absent or invalid."""
    match = FRONTMATTER.match(text)
    if not match:
        raise ValueError("missing YAML frontmatter")
    return yaml.load(match[1], Loader=UniqueLoader)
