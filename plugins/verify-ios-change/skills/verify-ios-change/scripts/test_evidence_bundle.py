"""Exercise the schema-6 evidence lifecycle without simulator access."""
import copy
import json
from pathlib import Path
import runpy
import subprocess
import tempfile
import unittest
from unittest.mock import patch


SCRIPTS = Path(__file__).resolve().parent
SKILL = SCRIPTS.parent
GENERATOR = runpy.run_path(str(SCRIPTS / "generate-report"))
VALIDATOR = runpy.run_path(str(SCRIPTS / "validate-manifest"))
# Stage 1 needs the jsonschema package or npx ajv-cli; without either it fails closed.
HAS_SCHEMA_VALIDATOR = VALIDATOR["check_file"](SKILL / "assets/manifest.json", structure_only=True)[0] == 0
needs_validator = unittest.skipUnless(HAS_SCHEMA_VALIDATOR, "needs jsonschema or npx ajv-cli")


class EvidenceBundleTests(unittest.TestCase):
    def setUp(self):
        self.scratch = tempfile.TemporaryDirectory(prefix="verify-ios-evidence-")
        self.addCleanup(self.scratch.cleanup)
        self.run = Path(self.scratch.name)
        self.manifest = json.loads((SKILL / "assets/manifest.json").read_text())
        self.manifest["run"].update(id="run.1", project_dir="/project", started_at="2026-10-11T00:00:00Z")

    def save(self, generate=False):
        (self.run / "manifest.json").write_text(json.dumps(self.manifest), encoding="utf-8")
        if generate:
            return GENERATOR["generate_report"](self.run)

    def validate(self, final=False):
        return VALIDATOR["validate"](self.run, self.manifest, final=final)

    def case(self, status="planned", case_id="TC1"):
        case = {
            "id": case_id, "title": "Toggle favourite", "rationale": "Changed interaction",
            "sources": ["PRD"], "preconditions": ["Item is not a favourite"],
            "steps": [{"action": "Tap favourite", "expected": "Favourite is on", "observed": None, "artifacts": []}],
            "status": status, "detail": None, "artifacts": [],
        }
        self.manifest["test_cases"].append(case)
        return case

    def driver(self):
        self.manifest["tools"] = [{"id": "tool.driver", "name": "Fixture driver", "version": "1", "roles": ["action_driver"]}]
        self.manifest["run"]["action_driver"] = "tool.driver"

    def passing_case(self):
        self.driver()
        case = self.case("pass")
        case["steps"][0].update(observed="Accessibility value is on", artifacts=["a.screen"])
        (self.run / "screen.png").write_bytes(b"fixture")
        self.manifest["artifacts"] = [{"id": "a.screen", "kind": "screenshot", "path": "screen.png"}]
        return case

    def test_empty_scaffold_is_valid_draft_without_html(self):
        self.assertEqual(self.validate(), [])
        self.assertTrue(self.validate(final=True))
        self.assertFalse((self.run / "index.html").exists())

    def test_planned_case_is_draft_only(self):
        self.case()
        self.save(generate=True)
        self.assertEqual(self.validate(), [])
        self.assertTrue(any("planned test case" in problem for problem in self.validate(final=True)))

    def test_prepare_only_report_is_valid_draft_without_cases(self):
        self.driver()
        self.manifest["checks"] = [
            {"id": "chk." + subject, "subject": subject, "status": "pass", "impact": None,
             "detail": "Observed ready", "artifacts": []}
            for subject in ("build", "simulator", "driver", "hierarchy", "lldb", "logs")
        ]
        self.manifest["checks"].append({
            "id": "chk.cleanup", "subject": "Cleanup", "status": "pass", "impact": None,
            "detail": "Run-owned sessions and processes stopped; app stopped; simulator booted",
            "artifacts": [],
        })
        report = self.save(generate=True)
        self.assertEqual(self.validate(), [])
        embedded = json.loads(VALIDATOR["SLOT"].search(report.read_text()).group(1))
        self.assertEqual(embedded, self.manifest)
        self.assertNotIn("change_context", embedded)
        self.assertEqual(embedded["test_cases"], [])
        self.assertTrue(any("empty final run" in problem for problem in self.validate(final=True)))

    def test_schema_five_is_rejected_without_changing_historical_bundle(self):
        self.passing_case()
        report = self.save(generate=True)
        original_report = report.read_bytes()
        self.manifest["schema"] = 5
        self.save()
        original_manifest = (self.run / "manifest.json").read_bytes()
        for script in ("generate-report", "validate-manifest"):
            with self.subTest(script=script):
                result = subprocess.run([str(SCRIPTS / script), str(self.run)], capture_output=True, text=True)
                self.assertEqual(result.returncode, 1)
                self.assertIn("schema 6", result.stdout + result.stderr)
                self.assertEqual((self.run / "manifest.json").read_bytes(), original_manifest)
                self.assertEqual(report.read_bytes(), original_report)

    def test_blocked_preparation_can_finish_without_cases_or_driver(self):
        self.manifest["checks"] = [{"id": "chk.build", "subject": "Build", "status": "fail", "impact": "blocker", "detail": "Compilation needs a source fix", "artifacts": []}]
        self.save(generate=True)
        self.assertEqual(self.validate(final=True), [])

    def test_partial_blocker_does_not_invalidate_passing_cases(self):
        self.passing_case()
        case = self.case("inconclusive", "TC2")
        case["detail"] = "Native hierarchy is unavailable"
        self.manifest["checks"] = [{"id": "chk.inspector", "subject": "Inspector", "status": "inconclusive", "impact": "blocker", "detail": "Needed only for TC2", "artifacts": []}]
        self.save(generate=True)
        self.assertEqual(self.validate(final=True), [])

    def test_validation_does_not_mutate_manifest(self):
        self.passing_case()
        before = copy.deepcopy(self.manifest)
        self.assertEqual(self.validate(), [])
        self.assertEqual(self.manifest, before)

    def test_passing_case_requires_observation_and_screenshot(self):
        self.driver()
        self.case("pass")
        problems = self.validate()
        self.assertTrue(any("observed results" in problem for problem in problems))
        self.assertTrue(any("screenshot" in problem for problem in problems))

    def test_nonpassing_results_need_explanation(self):
        for status in ("fail", "inconclusive", "withdrawn"):
            with self.subTest(status=status):
                self.manifest["test_cases"] = []
                self.case(status)
                self.assertTrue(any("detail: explain" in problem for problem in self.validate()))

    def test_failure_requires_exercised_observation_and_evidence(self):
        case = self.passing_case()
        case.update(status="fail", detail="Expected on but observed off")
        case["steps"][0].update(observed=None, artifacts=[])
        problems = self.validate()
        self.assertTrue(any("observed mismatch" in problem for problem in problems))
        self.assertTrue(any("fail requires evidence" in problem for problem in problems))
        case["steps"][0].update(observed="Accessibility value remains off", artifacts=["a.screen"])
        self.save(generate=True)
        self.assertEqual(self.validate(final=True), [])

    def test_withdrawal_preserves_supporting_evidence(self):
        case = self.case("withdrawn")
        case["detail"] = "Outside PRD scope"
        self.assertTrue(any("withdrawal requires evidence" in problem for problem in self.validate()))

    def test_unique_ids_and_all_reference_collections(self):
        case = self.case()
        self.manifest["test_cases"].append(copy.deepcopy(case))
        self.manifest["revisions"] = [{"id": "rev.1", "phase": "ordinary", "summary": "Change route", "test_cases": ["missing"], "artifacts": ["missing"]}]
        self.manifest["limitations"] = [{"description": "No logs", "test_cases": ["missing"], "artifacts": ["missing"]}]
        self.manifest["side_observations"] = [{"description": "Unrelated glitch", "test_cases": ["missing"], "artifacts": ["missing"]}]
        self.manifest["checks"] = [{"id": "chk.logs", "subject": "Logs", "status": "fail", "impact": "limitation", "detail": "No hook", "artifacts": ["missing"]}]
        problems = self.validate()
        self.assertTrue(any("duplicate ID" in problem for problem in problems))
        for collection in ("revisions", "limitations", "side_observations", "checks"):
            self.assertTrue(any(problem.startswith(collection) and "unknown" in problem for problem in problems))

    def test_artifact_must_exist_inside_run_directory(self):
        outside = self.run.parent / (self.run.name + "-outside")
        outside.write_text("private")
        self.addCleanup(outside.unlink)
        (self.run / "escape").symlink_to(outside)
        for path in ("missing.png", "../outside", "/absolute", "https://example.com/file", "escape", "a//b", "a/./b", "a\\b"):
            with self.subTest(path=path):
                self.manifest["artifacts"] = [{"id": "a.1", "kind": "other", "path": path}]
                self.assertTrue(any("artifacts[0].path" in problem for problem in self.validate()))

    def test_selected_driver_reference_and_role_must_match(self):
        self.driver()
        self.manifest["run"]["action_driver"] = "missing"
        self.assertTrue(any("run.action_driver" in problem for problem in self.validate()))
        self.manifest["run"]["action_driver"] = "tool.driver"
        self.manifest["tools"][0]["roles"] = ["diagnostic"]
        self.assertTrue(any("one tool" in problem for problem in self.validate()))
        self.driver()
        self.manifest["tools"].append({"id": "other", "name": "Other", "version": None, "roles": ["action_driver"]})
        self.assertTrue(any("one tool" in problem for problem in self.validate()))

    def modification(self, purpose="intervention", state="reverted"):
        change = {
            "description": "Temporary launch route after no eligible account or supported route was found",
            "purpose": purpose,
            "scope": "Real favourite handler and rendering; normal navigation and account eligibility unproven" if purpose == "intervention" else None,
            "state": state, "runtime_state": "Build fixture-1, PID 123; source restored, modified app retained",
            "restoration": "Rebuild restored source and reinstall on the selected UDID; reset the injected account fixture",
            "test_cases": ["TC1"], "result_cases": ["TC1"], "artifacts": ["a.patch"],
        }
        (self.run / "intervention.txt").write_text("Fixture intervention transcript")
        self.manifest["artifacts"].append({"id": "a.patch", "kind": "trace", "path": "intervention.txt"})
        self.manifest["temporary_modifications"].append(change)
        return change

    def assisted_case(self):
        case = self.passing_case()
        case.update(status="assisted_pass", detail="Favourite toggles under injected premium state; account eligibility unproven")
        self.manifest["run"]["effort"] = "high"
        self.manifest["revisions"] = [{
            "id": "rev.advanced", "phase": "advanced", "summary": "No eligible account; inject prerequisite state and invoke the real router",
            "test_cases": ["TC1"], "artifacts": [],
        }]
        self.modification()
        return case

    @needs_validator
    def test_assisted_pass_finishes_with_restored_source_and_retained_runtime(self):
        self.assisted_case()
        self.save(generate=True)
        self.assertEqual(self.check(final=True), (0, []))

    def test_diagnostic_cleanup_no_longer_controls_case_result(self):
        self.passing_case()
        change = self.modification(purpose="diagnostic")
        for state in ("reverted", "not_reverted", "runtime_only"):
            with self.subTest(state=state):
                change["state"] = state
                self.save(generate=True)
                self.assertEqual(self.validate(final=True), [])

    def test_assisted_pass_needs_normal_passing_evidence_and_explanation(self):
        case = self.assisted_case()
        case["detail"] = None
        case["steps"][0].update(observed=None, artifacts=[])
        problems = self.validate()
        for message in ("observed results", "screenshot", "detail: explain"):
            self.assertTrue(any(message in problem for problem in problems))

    def test_assisted_pass_requires_driver(self):
        self.assisted_case()
        self.manifest["run"]["action_driver"] = None
        self.manifest["tools"] = []
        self.assertTrue(any("selected action driver" in problem for problem in self.validate()))

    def test_assisted_pass_requires_linked_intervention_and_advanced_revision(self):
        self.assisted_case()
        change = self.manifest["temporary_modifications"][0]
        change["purpose"] = "diagnostic"
        self.assertTrue(any("linked intervention" in problem for problem in self.validate()))
        change["purpose"] = "intervention"
        self.manifest["revisions"] = []
        self.assertTrue(any("advanced recovery revision" in problem for problem in self.validate()))

    def test_intervention_scope_evidence_and_references_are_required(self):
        self.assisted_case()
        change = self.manifest["temporary_modifications"][0]
        change.update(scope=None, artifacts=[])
        problems = self.validate()
        self.assertTrue(any("scope/limits" in problem for problem in problems))
        self.assertTrue(any("intervention evidence" in problem for problem in problems))
        change.update(test_cases=["missing"], artifacts=["missing"])
        self.assertTrue(any("unknown test_cases" in problem for problem in self.validate()))
        self.assertTrue(any("unknown artifacts" in problem for problem in self.validate()))

    def test_intervention_cannot_be_reported_as_unqualified_pass(self):
        case = self.assisted_case()
        case.update(status="pass", detail=None)
        self.assertTrue(any("use assisted_pass" in problem for problem in self.validate()))

    @needs_validator
    def test_optional_normal_run_preserves_intervention_history(self):
        case = self.assisted_case()
        change = self.manifest["temporary_modifications"][0]
        case.update(status="pass", detail=None)
        case["steps"][0]["observed"] = "Independent normal build: accessibility value is on"
        change["result_cases"] = []
        self.save(generate=True)
        self.assertEqual(self.check(final=True), (0, []))
        self.assertEqual(change["test_cases"], ["TC1"])
        self.assertEqual(change["artifacts"], ["a.patch"])
        case.update(status="assisted_pass", detail="No longer depends on intervention")
        self.assertTrue(any("linked intervention" in problem for problem in self.validate()))

    def test_result_cases_must_be_affected_cases(self):
        self.assisted_case()
        self.case(case_id="TC2")
        self.manifest["temporary_modifications"][0]["result_cases"] = ["TC2"]
        self.assertTrue(any("subset of test_cases" in problem for problem in self.validate()))

    @needs_validator
    def test_advanced_recovery_effort_gate(self):
        self.assisted_case()
        for effort in (None, "low", "medium", "high", "xhigh", "max"):
            with self.subTest(effort=effort):
                self.manifest["run"]["effort"] = effort
                self.save(generate=True)
                code, problems = self.check(final=True)
                self.assertEqual(code, 0 if effort in ("high", "xhigh", "max") else 1, problems)
        self.manifest["run"]["effort"] = "ultra"
        self.save()
        self.assertEqual(self.check(structure_only=True)[0], 1)

    def test_advanced_attempts_require_effort_even_without_success(self):
        case = self.assisted_case()
        case.update(status="inconclusive", detail="Injected state could not be established")
        self.manifest["run"]["effort"] = None
        self.manifest["temporary_modifications"] = []
        self.assertTrue(any("run.effort" in problem for problem in self.validate()))

    def test_mixed_revision_phases_have_no_count_limit(self):
        self.assisted_case()
        self.manifest["revisions"] = [
            {"id": f"rev.{i}", "phase": "ordinary" if i < 6 else "advanced",
             "summary": "Distinct hypothesis after ordinary recovery exhausted", "test_cases": ["TC1"], "artifacts": []}
            for i in range(9)
        ]
        self.assertEqual(self.validate(), [])

    def test_ordinary_revisions_have_no_count_limit(self):
        self.case()
        self.manifest["revisions"] = [
            {"id": f"rev.{i}", "phase": "ordinary", "summary": "Evidence-backed approach",
             "test_cases": ["TC1"], "artifacts": []}
            for i in range(9)
        ]
        self.assertEqual(self.validate(), [])

    def test_runtime_only_intervention_and_cleanup_failure_preserve_result(self):
        case = self.assisted_case()
        change = self.manifest["temporary_modifications"][0]
        for state in ("runtime_only", "not_reverted"):
            with self.subTest(state=state):
                change["state"] = state
                self.manifest["checks"] = [{"id": "chk.cleanup", "subject": "Cleanup", "status": "fail", "impact": None,
                                            "detail": "Source restoration incomplete; modified app retained", "artifacts": []}]
                self.save(generate=True)
                self.assertEqual(self.validate(final=True), [])
                self.assertEqual(case["status"], "assisted_pass")

    def test_runtime_and_restoration_details_required_only_at_finish(self):
        self.assisted_case()
        self.manifest["temporary_modifications"][0].update(runtime_state=None, restoration=None)
        self.save(generate=True)
        self.assertEqual(self.validate(), [])
        problems = self.validate(final=True)
        for field in ("runtime_state", "restoration"):
            self.assertTrue(any(field in problem for problem in problems))

    def test_failed_and_inconclusive_interventions_keep_their_status(self):
        case = self.assisted_case()
        for status in ("fail", "inconclusive"):
            with self.subTest(status=status):
                case.update(status=status, detail="Observed mismatch" if status == "fail" else "Intervention could explain mismatch")
                self.save(generate=True)
                self.assertEqual(self.validate(final=True), [])

    def test_report_regeneration_escapes_script_text_and_preserves_evidence_links(self):
        self.passing_case()
        text = '<!--<script> and </script><script>alert("x")</script> and \\1 with café'
        self.manifest["test_cases"][0]["title"] = text
        report = self.save(generate=True)
        html = report.read_text()
        self.assertNotIn(text, html)
        self.assertNotIn("<", VALIDATOR["SLOT"].search(html).group(1))
        embedded = json.loads(VALIDATOR["SLOT"].search(html).group(1))
        self.assertEqual(embedded, self.manifest)
        self.assertEqual(self.validate(final=True), [])
        self.manifest["test_cases"][0]["title"] = "Updated title"
        self.save()
        self.assertTrue(any("differs" in problem for problem in self.validate(final=True)))
        self.assertEqual(self.validate(), [])
        self.save(generate=True)
        self.assertEqual(self.validate(final=True), [])

    def test_generator_failure_preserves_existing_report(self):
        report = self.save(generate=True)
        original = report.read_bytes()
        (self.run / "manifest.json").write_text("invalid JSON")
        with self.assertRaises(ValueError):
            GENERATOR["generate_report"](self.run)
        self.assertEqual(report.read_bytes(), original)
        self.save()
        with patch.dict(GENERATOR["generate_report"].__globals__, TEMPLATE=self.run / "missing-template"):
            with self.assertRaises(OSError):
                GENERATOR["generate_report"](self.run)
        self.assertEqual(report.read_bytes(), original)
        with patch.object(Path, "replace", side_effect=PermissionError("denied")):
            with self.assertRaises(PermissionError):
                GENERATOR["generate_report"](self.run)
        self.assertEqual(report.read_bytes(), original)
        self.assertEqual(list(self.run.glob(".index-*")), [])

    def test_final_report_and_run_identity_are_required(self):
        self.manifest["checks"] = [{"id": "chk.input", "subject": "Requirements", "status": "inconclusive", "impact": "blocker", "detail": "Requirements unavailable", "artifacts": []}]
        self.manifest["run"]["id"] = None
        problems = self.validate(final=True)
        self.assertTrue(any("run.id" in problem for problem in problems))
        self.assertTrue(any("index.html" in problem for problem in problems))

    def test_recovered_check_has_only_latest_result(self):
        check = {"id": "chk.build", "subject": "Build", "status": "fail", "impact": "blocker", "detail": "Needs setup", "artifacts": []}
        self.manifest["checks"] = [check]
        self.passing_case()
        check.update(status="pass", impact=None, detail=None)
        self.save(generate=True)
        self.assertEqual(self.validate(final=True), [])
        self.assertEqual(len(self.manifest["checks"]), 1)

    def test_invalid_check_impact(self):
        self.case()
        self.manifest["checks"] = [{"id": "chk.build", "subject": "Build", "status": "pass", "impact": "blocker", "detail": None, "artifacts": []}]
        self.manifest["revisions"] = [{"id": f"rev.{i}", "phase": "ordinary", "summary": "Retry", "test_cases": ["TC1"], "artifacts": []} for i in range(4)]
        problems = self.validate()
        self.assertTrue(any("requires fail or inconclusive" in problem for problem in problems))

    def check(self, **options):
        return VALIDATOR["check_file"](self.run, **options)

    @needs_validator
    def test_starter_manifest_and_valid_plan_pass_the_schema(self):
        self.save()
        self.assertEqual(self.check(), (0, []))
        self.passing_case()
        self.save()
        self.assertEqual(self.check(), (0, []))

    @needs_validator
    def test_schema_stage_reports_every_structural_problem_with_its_location(self):
        case = self.case()
        case["status"] = "passed"
        case["extra"] = 1
        case["steps"][0]["observed"] = 5
        self.manifest["artifacts"] = [{"id": "bad id", "kind": "photo", "path": "a.png"}]
        self.manifest["run"]["started_at"] = "yesterday"
        self.save()
        code, problems = self.check()
        text = "\n".join(problems)
        self.assertEqual(code, 1)
        for where in ("test_cases[0].status", "test_cases[0]", "test_cases[0].steps[0].observed",
                      "artifacts[0].id", "artifacts[0].kind", "run.started_at"):
            self.assertIn(where, text)
        self.assertIn("extra", text)

    @needs_validator
    def test_structure_only_skips_reference_and_evidence_checks(self):
        case = self.case()
        case["artifacts"] = ["a.missing"]
        self.save()
        self.assertEqual(self.check(structure_only=True), (0, []))
        code, problems = self.check()
        self.assertEqual(code, 1)
        self.assertTrue(any("a.missing" in problem for problem in problems))

    @needs_validator
    def test_structural_errors_hide_cascading_reference_errors(self):
        case = self.case()
        case["status"] = "passed"
        case["artifacts"] = ["a.missing"]
        self.save()
        code, problems = self.check()
        self.assertEqual(code, 1)
        self.assertFalse(any("unknown artifacts ID" in problem for problem in problems))

    @needs_validator
    def test_paths_are_parameters(self):
        self.passing_case()
        self.save(generate=True)
        manifest = self.run / "manifest.json"
        self.assertEqual(self.check(), (0, []))
        self.assertEqual(VALIDATOR["check_file"](manifest), (0, []))
        # Move the report and evidence out of the manifest's directory.
        other = self.run / "elsewhere"
        other.mkdir()
        (self.run / "screen.png").rename(other / "screen.png")
        (self.run / "index.html").rename(other / "report.html")
        self.assertEqual(self.check(final=True)[0], 1)
        self.assertEqual(self.check(final=True, root=other, report=other / "report.html"), (0, []))
        # A caller-supplied schema replaces the skill's.
        strict = self.run / "strict.schema.json"
        strict.write_text(json.dumps({"type": "object", "required": ["nope"]}))
        code, problems = self.check(schema=strict)
        self.assertEqual(code, 1)
        self.assertIn("nope", "\n".join(problems))

    def test_missing_validator_fails_closed(self):
        self.save()
        with patch.dict("sys.modules", {"jsonschema": None}), patch.object(VALIDATOR["shutil"], "which", return_value=None):
            code, problems = self.check()
            self.assertEqual(code, 3)
            self.assertIn("jsonschema", problems[0])

    def test_unreadable_schema_is_an_input_error(self):
        self.save()
        schema = self.run / "broken.schema.json"
        schema.write_text("invalid JSON")
        self.assertEqual(self.check(schema=schema)[0], 2)
        self.assertEqual(self.check(schema=self.run / "missing.schema.json")[0], 2)

    @needs_validator
    def test_cli_errors_and_final_mode(self):
        self.save()
        for script in ("generate-report", "validate-manifest"):
            with self.subTest(script=script):
                result = subprocess.run([str(SCRIPTS / script), str(self.run)], capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        result = subprocess.run([str(SCRIPTS / "validate-manifest"), "--final", str(self.run)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 1)
        self.assertIn("empty final run", result.stdout)
        (self.run / "manifest.json").write_text('{"schema": 3}')
        result = subprocess.run([str(SCRIPTS / "generate-report"), str(self.run)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 1)
        self.assertIn("schema 6", result.stderr)
        (self.run / "manifest.json").write_text("invalid JSON")
        result = subprocess.run([str(SCRIPTS / "validate-manifest"), str(self.run)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 2)


if __name__ == "__main__":
    unittest.main()
