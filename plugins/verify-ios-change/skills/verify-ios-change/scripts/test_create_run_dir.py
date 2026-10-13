"""Run with: python3 -m unittest discover -s <skill>/scripts -p 'test_*.py'."""
from contextlib import redirect_stderr
import io
import json
import os
from pathlib import Path
import re
import runpy
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import patch


SCRIPT = Path(__file__).with_name("create-run-dir").resolve()
SKILL = SCRIPT.parent.parent / "SKILL.md"
RESOLVER = runpy.run_path(str(SCRIPT))


class RunDirectoryTests(unittest.TestCase):
    def setUp(self):
        self.scratch = tempfile.TemporaryDirectory(prefix="verify-ios-test-")
        self.addCleanup(self.scratch.cleanup)
        self.scratch_dir = Path(self.scratch.name).resolve()
        self.project_dir = self.scratch_dir / "Project name"
        self.project_dir.mkdir()
        self.git("init", "-q")
        self.temp_dir = self.scratch_dir / "temp"
        self.temp_dir.mkdir()
        self.env = dict(os.environ)
        self.env.pop("VERIFY_IOS_CHANGE_ROOT", None)
        self.env.update(TMPDIR=str(self.temp_dir), TEMP=str(self.temp_dir), TMP=str(self.temp_dir))

    def git(self, *args):
        return subprocess.run(
            ["git", "-C", str(self.project_dir), *args],
            check=True, capture_output=True, text=True,
        )

    def worktree(self):
        self.git(
            "-c", "user.name=Test", "-c", "user.email=test@example.invalid",
            "-c", "commit.gpgsign=false", "-c", "core.hooksPath=/dev/null",
            "commit", "-qm", "fixture", "--allow-empty",
        )
        worktree_dir = self.scratch_dir / "linked checkout"
        self.git("worktree", "add", "--detach", str(worktree_dir))
        return worktree_dir

    def invoke(self, *, project_dir=None, cwd=None, args=None):
        result = subprocess.run(
            [str(SCRIPT), *(args if args is not None else [str(project_dir or self.project_dir)])],
            cwd=cwd or self.scratch_dir, env=self.env, capture_output=True, text=True,
        )
        if result.returncode:
            self.assertEqual(result.returncode, 1)
            self.assertEqual(result.stdout, "")
            return result.stderr
        self.assertEqual(result.stderr, "")
        return result.stdout

    def assert_failure(self, output):
        lines = output.splitlines()
        self.assertEqual(len(lines), 2)
        self.assertTrue(lines[0].startswith("ERROR: Could not create run directory: "))
        self.assertEqual(lines[1], RESOLVER["RECOVERY"])

    def test_default_is_existing_writable_absolute_directory(self):
        output = self.invoke()
        runs_dir = Path(output.strip())
        self.assertEqual(output, str(runs_dir) + "\n")
        self.assertEqual(runs_dir.parent, self.temp_dir / "Project-name/verify-ios-change/runs")
        self.assertRegex(runs_dir.name, r"^\d{8}T\d{6}\.\d{6}Z$")
        self.assertTrue(runs_dir.is_absolute())
        self.assertEqual([path.name for path in runs_dir.iterdir()], ["manifest.json"])
        manifest = json.loads((runs_dir / "manifest.json").read_text())
        self.assertEqual(manifest["schema"], 6)
        self.assertEqual(manifest["run"]["id"], runs_dir.name)
        self.assertIsNone(manifest["run"]["session_id"])
        self.assertEqual(manifest["run"]["project_dir"], str(self.project_dir))
        self.assertRegex(manifest["run"]["started_at"], r"^\d{4}-\d{2}-\d{2}T.*Z$")
        self.assertNotIn("finished_at", manifest["run"])
        self.assertEqual(manifest["test_cases"], [])
        self.assertEqual(manifest["checks"], [])
        with tempfile.TemporaryFile(dir=runs_dir) as probe:
            probe.write(b"evidence")

    def test_session_id_is_recorded_and_empty_stays_null(self):
        for args, expected in (("abc-123",), "abc-123"), (("",), None):
            with self.subTest(session_id=expected):
                run_dir = Path(self.invoke(args=[str(self.project_dir), *args]).strip())
                manifest = json.loads((run_dir / "manifest.json").read_text())
                self.assertEqual(manifest["run"]["session_id"], expected)

    def test_shell_navigation_does_not_change_project_identity(self):
        other_dir = self.scratch_dir / "other repository"
        subprocess.run(["git", "init", "-q", str(other_dir)], check=True)
        self.assertEqual(Path(self.invoke().strip()).parent, Path(self.invoke(cwd=other_dir).strip()).parent)

    def test_linked_worktree_shares_main_checkout_directory(self):
        self.assertEqual(Path(self.invoke().strip()).parent, Path(self.invoke(project_dir=self.worktree()).strip()).parent)

    def test_runs_are_distinct_siblings_in_one_directory(self):
        first = Path(self.invoke().strip())
        second = Path(self.invoke().strip())
        self.assertEqual(first.parent, self.temp_dir / "Project-name/verify-ios-change/runs")
        self.assertEqual(first.parent, second.parent)
        self.assertNotEqual(first, second)
        self.assertTrue(first.is_dir())
        self.assertTrue(second.is_dir())

    def test_timestamp_collision_preserves_existing_directory(self):
        from datetime import datetime, timezone
        parent = self.scratch_dir / "runs"
        parent.mkdir()
        first = datetime(2026, 10, 11, tzinfo=timezone.utc)
        second = datetime(2026, 10, 11, microsecond=1, tzinfo=timezone.utc)
        existing = parent / first.strftime("%Y%m%dT%H%M%S.%fZ")
        existing.mkdir()
        marker = existing / "evidence"
        marker.write_text("keep")
        from unittest.mock import Mock
        clock = Mock()
        clock.now.side_effect = [first, second]
        with patch.dict(RESOLVER["create_run_dir"].__globals__, resolve_runs_dir=lambda _: parent, datetime=clock):
            created = RESOLVER["create_run_dir"](self.project_dir)
        self.assertEqual(created, parent / second.strftime("%Y%m%dT%H%M%S.%fZ"))
        self.assertTrue(created.is_dir())
        self.assertEqual(marker.read_text(), "keep")

    def test_both_worktree_and_main_checkout_are_rejected(self):
        worktree_dir = self.worktree()
        for checkout_dir in (self.project_dir, worktree_dir):
            with self.subTest(checkout=checkout_dir):
                self.env["TMPDIR"] = str(checkout_dir)
                self.assert_failure(self.invoke(project_dir=worktree_dir))
                self.assertFalse((checkout_dir / "Project-name").exists())

    def test_symlink_into_checkout_is_rejected(self):
        alias = self.scratch_dir / "alias"
        alias.symlink_to(self.project_dir, target_is_directory=True)
        self.env["TMPDIR"] = str(alias)
        self.assert_failure(self.invoke())
        self.assertFalse((self.project_dir / "Project-name").exists())

    def test_platform_temp_inside_checkout_is_rejected(self):
        self.env["TMPDIR"] = str(self.project_dir)
        self.assert_failure(self.invoke())
        self.assertFalse((self.project_dir / "Project-name").exists())

    def test_existing_file_reports_failure(self):
        blocker = self.temp_dir / "Project-name"
        blocker.write_text("keep")
        self.assert_failure(self.invoke())
        self.assertEqual(blocker.read_text(), "keep")

    def test_unwritable_destination_reports_failure(self):
        # Inject a permission failure so this check also works under root.
        output = io.StringIO()
        with patch.dict(os.environ, self.env, clear=True), patch.object(
            RESOLVER["sys"], "argv", [str(SCRIPT), str(self.project_dir)]
        ), patch.object(RESOLVER["tempfile"], "tempdir", str(self.temp_dir)), patch.object(
            RESOLVER["tempfile"], "TemporaryFile", side_effect=PermissionError("denied")
        ), redirect_stderr(output):
            self.assertEqual(RESOLVER["main"](), 1)
        self.assert_failure(output.getvalue())
        self.assertIn("denied", output.getvalue())

    def test_missing_argument_and_invalid_project_report_failure(self):
        self.assert_failure(self.invoke(args=[]))
        self.assert_failure(self.invoke(args=[str(self.project_dir), "id", "extra"]))
        self.assert_failure(self.invoke(project_dir=self.scratch_dir / "missing"))

    def test_missing_or_invalid_template_does_not_create_a_run(self):
        template = self.scratch_dir / "manifest.json"
        for contents in (None, "invalid JSON", '{"schema": 3}', '{"schema": 4}'):
            with self.subTest(contents=contents):
                if contents is not None:
                    template.write_text(contents)
                with patch.dict(RESOLVER["create_run_dir"].__globals__, TEMPLATE=template):
                    with self.assertRaises((OSError, ValueError)):
                        RESOLVER["create_run_dir"](self.project_dir)
                self.assertFalse((self.temp_dir / "Project-name").exists())

    def test_manifest_write_failure_removes_partial_run(self):
        parent = self.scratch_dir / "runs"
        parent.mkdir()
        with patch.dict(RESOLVER["create_run_dir"].__globals__, resolve_runs_dir=lambda _: parent):
            with patch.object(Path, "write_text", side_effect=PermissionError("denied")):
                with self.assertRaises(PermissionError):
                    RESOLVER["create_run_dir"](self.project_dir)
        self.assertEqual(list(parent.iterdir()), [])

    def test_old_override_is_not_an_alias(self):
        self.env["VERIFY_IOS_CHANGE_ROOT"] = str(self.scratch_dir / "old")
        self.assertEqual(Path(self.invoke().strip()).parent, self.temp_dir / "Project-name/verify-ios-change/runs")
        self.assertFalse((self.scratch_dir / "old").exists())

    def test_documented_command_handles_spaces_in_script_and_project_paths(self):
        skill_dir = self.scratch_dir / "skill with spaces"
        scripts_dir = skill_dir / "scripts"
        scripts_dir.mkdir(parents=True)
        shutil.copy2(SCRIPT, scripts_dir / SCRIPT.name)
        assets_dir = skill_dir / "assets"
        assets_dir.mkdir()
        shutil.copy2(SCRIPT.parent.parent / "assets/manifest.json", assets_dir / "manifest.json")
        command = re.search(r"```sh\n\s*([^\n]+)\n\s*```", SKILL.read_text()).group(1)
        command = command.replace("${CLAUDE_SKILL_DIR}", str(skill_dir))
        command = command.replace("${CLAUDE_PROJECT_DIR}", str(self.project_dir))
        command = command.replace("${CLAUDE_SESSION_ID}", "session-1")
        result = subprocess.run(
            ["bash", "-c", command], cwd=self.scratch_dir, env=self.env,
            capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stderr, "")
        self.assertEqual(Path(result.stdout.strip()).parent, Path(self.invoke().strip()).parent)
        run_dir = Path(result.stdout.strip())
        self.assertTrue(run_dir.is_dir())
        self.assertEqual(json.loads((run_dir / "manifest.json").read_text())["run"]["session_id"], "session-1")


if __name__ == "__main__":
    unittest.main()
