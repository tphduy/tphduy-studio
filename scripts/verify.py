#!/usr/bin/env python3
"""Check repository conventions and invoke Claude's native validator."""

import argparse
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
from urllib.parse import unquote, urlsplit

import yaml

NAME = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")
NUMBER = r"(?:0|[1-9]\d*)"
PRERELEASE = rf"(?:{NUMBER}|[0-9A-Za-z-]*[A-Za-z-][0-9A-Za-z-]*)"
VERSION = re.compile(rf"{NUMBER}\.{NUMBER}\.{NUMBER}(?:-{PRERELEASE}(?:\.{PRERELEASE})*)?(?:\+[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?")
CATALOGS = {
    "codex": ".agents/plugins/marketplace.json",
    "claude": ".claude-plugin/marketplace.json",
}


def unique_pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate key: {key}")
        result[key] = value
    return result


class UniqueLoader(yaml.SafeLoader):
    pass


def yaml_mapping(loader, node):
    loader.flatten_mapping(node)
    return unique_pairs((loader.construct_object(k), loader.construct_object(v)) for k, v in node.value)


UniqueLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, yaml_mapping)


class Verifier:
    def __init__(self, root):
        self.root = Path(root).resolve()
        self.results = []

    def record(self, status, check, detail):
        self.results.append({"status": status, "check": check, "detail": str(detail)})

    def load_json(self, path):
        try:
            value = json.loads(path.read_text(), object_pairs_hook=unique_pairs)
            if not isinstance(value, dict):
                raise ValueError("expected a JSON object")
            return value
        except (OSError, ValueError) as error:
            self.record("failed", str(path.relative_to(self.root)), error)
            return None

    def contained(self, base, value, check):
        if not isinstance(value, str) or not value.startswith("./"):
            raise ValueError(f"{check}: expected a ./-prefixed path")
        path = (base / value).resolve()
        if not path.is_relative_to(base.resolve()):
            raise ValueError(f"{check}: path escapes its root: {value}")
        if not path.exists():
            raise ValueError(f"{check}: missing path: {value}")
        return path

    def manifest_paths(self, value, base):
        if isinstance(value, dict):
            for child in value.values():
                self.manifest_paths(child, base)
        elif isinstance(value, list):
            for child in value:
                self.manifest_paths(child, base)
        elif isinstance(value, str) and value.startswith("./"):
            self.contained(base, value, "manifest reference")

    def manifest(self, plugin, platform, name):
        path = plugin / ("plugin.json" if platform == "codex" else ".claude-plugin/plugin.json")
        data = self.load_json(path)
        if data is None:
            return None
        try:
            if data.get("name") != name:
                raise ValueError("catalog and manifest names differ")
            if not VERSION.fullmatch(str(data.get("version", ""))):
                raise ValueError("expected a semantic version")
            if not isinstance(data.get("description"), str) or not data["description"].strip():
                raise ValueError("missing description")
            if not isinstance(data.get("author"), dict) or not data["author"].get("name"):
                raise ValueError("missing author.name")
            if platform == "codex":
                if data.get("$schema") != "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json":
                    raise ValueError("expected the portable Agent Plugins schema")
                if any(key in data for key in ("skills", "mcpServers", "apps", "interface")):
                    raise ValueError("portable components use fixed paths or extensions.com.openai")
            self.manifest_paths(data, plugin)
            self.record("pass", f"{platform} manifest {name}", data["version"])
        except ValueError as error:
            self.record("failed", f"{platform} manifest {name}", error)
        return data

    def structure(self):
        catalogs, bundles, manifests = {}, {}, {}
        for platform, relative in CATALOGS.items():
            catalog = self.load_json(self.root / relative)
            if catalog is None:
                continue
            catalogs[platform] = catalog
            try:
                if not NAME.fullmatch(str(catalog.get("name", ""))):
                    raise ValueError("invalid marketplace name")
                if platform == "claude" and not catalog.get("owner", {}).get("name"):
                    raise ValueError("missing owner.name")
                if not isinstance(catalog.get("plugins"), list):
                    raise ValueError("plugins must be an array")
                seen = set()
                for entry in catalog["plugins"]:
                    if not isinstance(entry, dict):
                        raise ValueError("plugin entry must be an object")
                    name = entry.get("name", "")
                    if not isinstance(name, str) or not NAME.fullmatch(name) or len(name) > 64:
                        raise ValueError("invalid plugin name")
                    if name in seen:
                        raise ValueError(f"duplicate plugin: {name}")
                    seen.add(name)
                    if "version" in entry:
                        raise ValueError(f"{name}: keep version in the manifest only")
                    source = entry.get("source")
                    if platform == "codex":
                        if not isinstance(source, dict) or source.get("source") != "local":
                            raise ValueError(f"{name}: this repository expects local directory sources")
                        policy = entry.get("policy", {})
                        if policy.get("installation") not in {"AVAILABLE", "INSTALLED_BY_DEFAULT", "NOT_AVAILABLE"}:
                            raise ValueError(f"{name}: invalid installation policy")
                        if policy.get("authentication") not in {"ON_INSTALL", "ON_USE"}:
                            raise ValueError(f"{name}: invalid authentication policy")
                        if not isinstance(entry.get("category"), str) or not entry["category"].strip():
                            raise ValueError(f"{name}: missing category")
                        source = source.get("path")
                    plugin = self.contained(self.root, source, name)
                    if plugin != self.root / "plugins" / name or not plugin.is_dir():
                        raise ValueError(f"{name}: expected plugins/{name}/")
                    bundles[name] = plugin
                    data = self.manifest(plugin, platform, name)
                    if data is not None:
                        manifests.setdefault(name, []).append(data)
                self.record("pass", f"{platform} catalog", f"{len(seen)} plugin(s)")
            except (ValueError, TypeError, AttributeError) as error:
                self.record("failed", f"{platform} catalog", error)
        if len(catalogs) == 2 and catalogs["codex"].get("name") != catalogs["claude"].get("name"):
            self.record("failed", "marketplace identity", "catalog names differ")
        for name, values in manifests.items():
            for field in ("name", "description", "author", "version", "license"):
                if any(value.get(field) != values[0].get(field) for value in values[1:]):
                    self.record("failed", f"metadata {name}", f"{field} differs between manifests")
        plugins_dir = self.root / "plugins"
        if plugins_dir.exists():
            for plugin in plugins_dir.iterdir():
                if plugin.is_dir() and plugin.name not in bundles:
                    self.record("failed", "catalog membership", f"uncataloged plugin: {plugin.name}")
        for name, plugin in bundles.items():
            for path in plugin.rglob("*"):
                if not path.resolve().is_relative_to(plugin):
                    self.record("failed", f"bundle {name}", f"path escapes plugin: {path.name}")
                    continue
                if path.is_file() and path.suffix == ".json" and path.name != "plugin.json":
                    self.load_json(path)
            skills_dir = plugin / "skills"
            if skills_dir.exists() and not skills_dir.is_dir():
                self.record("failed", f"bundle {name}", "skills must be a directory")
                continue
            for directory in skills_dir.glob("*"):
                if directory.is_dir() and not directory.name.startswith(".") and not (directory / "SKILL.md").is_file():
                    self.record("failed", f"skill {name}/{directory.name}", "missing SKILL.md")
            for skill in skills_dir.glob("*/SKILL.md"):
                try:
                    if not skill.resolve().is_relative_to(plugin):
                        raise ValueError("skill path escapes plugin")
                    text = skill.read_text()
                    match = re.match(r"\A---\r?\n(.*?)\r?\n---(?:\r?\n|$)", text, re.S)
                    if not match:
                        raise ValueError("missing YAML frontmatter")
                    data = yaml.load(match[1], Loader=UniqueLoader)
                    if not isinstance(data, dict) or data.get("name") != skill.parent.name:
                        raise ValueError("skill name must match its directory")
                    if not NAME.fullmatch(data["name"]) or len(data["name"]) > 64:
                        raise ValueError("invalid skill name")
                    if not isinstance(data.get("description"), str) or not data["description"].strip():
                        raise ValueError("missing skill description")
                    self.record("pass", f"skill {name}/{skill.parent.name}", "valid frontmatter")
                except (OSError, ValueError, yaml.YAMLError) as error:
                    self.record("failed", f"skill {name}/{skill.parent.name}", error)
        self.markdown(bundles)
        try:
            if (self.root / "CLAUDE.md").read_text().strip() != "@AGENTS.md":
                raise ValueError("CLAUDE.md must import shared instructions")
            if not (self.root / "AGENTS.md").is_file():
                raise ValueError("missing AGENTS.md")
            settings = self.load_json(self.root / ".claude/settings.json")
            if settings is None or settings.get("enabledPlugins", {}).get("plugin-dev@claude-plugins-official") is not True:
                raise ValueError("project must enable upstream plugin-dev")
            self.record("pass", "maintenance setup", "shared instructions and Claude authoring dependency")
        except (OSError, ValueError) as error:
            self.record("failed", "maintenance setup", error)

    def markdown(self, bundles):
        files = list(self.root.glob("*.md")) + list((self.root / "docs").rglob("*.md"))
        for plugin in bundles.values():
            files.extend(plugin.rglob("*.md"))
        for path in files:
            base = next((plugin for plugin in bundles.values() if path.is_relative_to(plugin)), self.root)
            try:
                if not path.resolve().is_relative_to(base):
                    raise ValueError("Markdown file escapes its root")
                text = path.read_text()
                for target in re.findall(r"!?\[[^\]]*\]\(([^\n)]*)\)", text):
                    target = target.strip()
                    if target.startswith("<"):
                        target = target[1:target.find(">")]
                    else:
                        target = target.split()[0] if target else ""
                    url = urlsplit(target)
                    if url.scheme or url.netloc or not url.path:
                        continue
                    destination = (path.parent / unquote(url.path)).resolve()
                    if not destination.is_relative_to(base) or not destination.exists():
                        raise ValueError(f"missing or escaping local link: {target}")
            except (OSError, ValueError) as error:
                self.record("failed", str(path.relative_to(self.root)), error)
        self.record("pass", "Markdown scan", f"scanned {len(files)} file(s); link failures reported separately")

    def native(self, skip=False):
        if skip or not shutil.which("claude"):
            self.record("inconclusive", "Claude native validation", "skipped" if skip else "claude is not installed")
            return
        targets = [self.root / CATALOGS["claude"]]
        catalog = self.load_json(targets[0])
        if catalog is not None and isinstance(catalog.get("plugins"), list):
            targets.extend(self.root / "plugins" / entry["name"] for entry in catalog["plugins"] if isinstance(entry, dict) and isinstance(entry.get("name"), str) and NAME.fullmatch(entry["name"]))
        for target in targets:
            check = f"Claude validate {target.relative_to(self.root)}"
            try:
                process = subprocess.run(["claude", "plugin", "validate", str(target), "--strict", "--json"], capture_output=True, text=True, timeout=60)
            except (OSError, subprocess.TimeoutExpired) as error:
                self.record("inconclusive", "Claude native validation", error)
                continue
            if process.returncode == 2:
                self.record("inconclusive", check, f"validator hit an unexpected error: {process.stderr.strip()}")
                continue
            try:
                report = json.loads(process.stdout)
                problems = [*report["manifest"]["errors"], *report["manifest"]["warnings"]]
                for item in report.get("contents", []):
                    problems += [*item.get("errors", []), *item.get("warnings", [])]
                passed = report["success"] is True and process.returncode == 0 and not problems
            except (ValueError, KeyError, TypeError, AttributeError) as error:
                self.record("failed", check, f"unreadable validator JSON: {error}")
                continue
            self.record("pass" if passed else "failed", check, "success: true, no errors or warnings" if passed else f"exit {process.returncode}: {problems or process.stdout.strip()}")

    def report(self):
        statuses = {item["status"] for item in self.results}
        status = "failed" if "failed" in statuses else "inconclusive" if "inconclusive" in statuses else "pass"
        return {"status": status, "checks": self.results}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--skip-native", action="store_true")
    args = parser.parse_args()
    verifier = Verifier(args.root)
    verifier.structure()
    verifier.native(args.skip_native)
    report = verifier.report()
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        for item in report["checks"]:
            print(f"{item['status']}: {item['check']}: {item['detail']}")
        print(f"{report['status']}: overall")
    return {"pass": 0, "failed": 1, "inconclusive": 2}[report["status"]]


if __name__ == "__main__":
    sys.exit(main())
