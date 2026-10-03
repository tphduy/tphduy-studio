"""Exercise failures that could otherwise produce a broken distributable package."""

import importlib.util
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("verify", ROOT / "scripts/verify.py")
verify = importlib.util.module_from_spec(spec)
spec.loader.exec_module(verify)


class VerifyTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        for name in (".agents", ".claude-plugin", ".claude", "plugins", "docs"):
            shutil.copytree(ROOT / name, self.root / name)
        for name in ("AGENTS.md", "CLAUDE.md", "README.md", "LICENSE"):
            shutil.copy2(ROOT / name, self.root / name)

    def structure(self):
        checker = verify.Verifier(self.root)
        checker.structure()
        return checker

    def change_json(self, relative, change):
        path = self.root / relative
        data = json.loads(path.read_text())
        change(data)
        path.write_text(json.dumps(data))

    def assert_failed(self, fragment):
        checker = self.structure()
        self.assertEqual(checker.report()["status"], "failed")
        self.assertTrue(any(fragment in x["detail"] for x in checker.results if x["status"] == "failed"), checker.results)

    def test_current_package(self):
        self.assertEqual(self.structure().report()["status"], "pass")

    def test_manifest_version_drift(self):
        self.change_json("plugins/writing-for-human/plugin.json", lambda d: d.update(version="0.2.0"))
        self.assert_failed("version differs")

    def test_duplicate_catalog_entry(self):
        self.change_json(".claude-plugin/marketplace.json", lambda d: d["plugins"].append(d["plugins"][0]))
        self.assert_failed("duplicate plugin")

    def test_catalog_source_escape(self):
        self.change_json(".claude-plugin/marketplace.json", lambda d: d["plugins"][0].update(source="./../"))
        self.assert_failed("escapes")

    def test_missing_component(self):
        self.change_json("plugins/writing-for-human/.claude-plugin/plugin.json", lambda d: d.update(hooks="./missing.json"))
        self.assert_failed("missing path")

    def test_broken_reference(self):
        (self.root / "plugins/writing-for-human/skills/writing-for-human/references/jokes.md").unlink()
        self.assert_failed("missing or escaping local link")

    def test_duplicate_yaml_field(self):
        path = self.root / "plugins/writing-for-human/skills/writing-for-human/SKILL.md"
        path.write_text(path.read_text().replace("name: writing-for-human", "name: writing-for-human\nname: duplicate"))
        self.assert_failed("duplicate key")

    def test_missing_skill_entrypoint(self):
        (self.root / "plugins/writing-for-human/skills/writing-for-human/SKILL.md").unlink()
        self.assert_failed("missing SKILL.md")

    def test_invalid_semantic_version(self):
        self.change_json("plugins/writing-for-human/plugin.json", lambda d: d.update(version="0.1.0-01"))
        self.assert_failed("semantic version")

    def test_missing_native_tool_is_inconclusive(self):
        checker = self.structure()
        with patch.object(verify.shutil, "which", return_value=None):
            checker.native()
        self.assertEqual(checker.report()["status"], "inconclusive")


if __name__ == "__main__":
    unittest.main()
