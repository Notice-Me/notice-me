"""Offline fixtures only: these tests do not establish any external AI review."""

import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from devtools.ai_workflow.workflow import Run, WorkflowError, policy, safe_text


class WorkflowTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.git("init", "-q", "-b", "feat/test")
        (self.root / ".gitignore").write_text(".ai-workflow/\n__pycache__/\n", encoding="utf-8")
        (self.root / "server").mkdir()
        (self.root / "server/code.py").write_text("value = 1\n", encoding="utf-8")
        self.git("add", ".")
        self.git(
            "-c",
            "user.name=Offline",
            "-c",
            "user.email=offline@example.invalid",
            "-c",
            "commit.gpgsign=false",
            "-c",
            f"core.hooksPath={self.root / 'no-hooks'}",
            "commit",
            "-qm",
            "offline fixture",
        )
        self.git("update-ref", "refs/remotes/origin/main", "HEAD")
        self.spec = self.root / "spec.json"
        self.spec.write_text(
            json.dumps(
                {
                    "goal": "Offline fixture",
                    "acceptance": ["Do not call models"],
                    "allowed_paths": ["server", "spec.json"],
                    "context_files": [],
                }
            ),
            encoding="utf-8",
        )
        self.run = Run(self.root, "fixture")
        self.state = self.run.create(self.spec)

    def git(self, *args):
        return subprocess.run(["git", "-C", str(self.root), *args], capture_output=True, check=True)

    def file(self, data, name="input.json"):
        path = self.root / name
        path.write_text(json.dumps(data), encoding="utf-8")
        return path

    def review(self, role="gemini", **updates):
        state, _ = self.run.load()
        data = {
            "role": role,
            "iteration": state["iteration"],
            "request_hash": state["request_hash"],
            "provenance": "MANUAL_MODEL_EXPORT",
            "model_label": "SYNTHETIC_TEST_FIXTURE_NOT_REAL_MODEL",
            "verdict": "approve",
            "findings": [],
            "usage": {"input_tokens": None, "output_tokens": None, "cost_usd": None},
        }
        data.update(updates)
        # Ignored local run path keeps test input outside approved repo changes.
        path = self.run.path / f"test-{role}.json"
        path.write_text(json.dumps(data), encoding="utf-8")
        return path

    def reviewers(self):
        self.run.import_review("gemini", self.review("gemini"))
        self.run.import_review("claude", self.review("claude"))

    def decision(self, **updates):
        state, _ = self.run.load()
        data = {
            "actor": "USER",
            "request_hash": state["request_hash"],
            "review_hashes": {r: x["sha256"] for r, x in state["reviews"].items()},
            "verdict": "approve",
            "synthesis_by": "user",
            "rationale": "Synthetic local test attestation only",
            "resolved_findings": {},
            "allowed_paths": state["allowed_paths"],
        }
        data.update(updates)
        path = self.run.path / "test-decision.json"
        path.write_text(json.dumps(data), encoding="utf-8")
        return path

    def approve(self):
        self.reviewers()
        return self.run.decide(self.decision())

    def check(self, code=0):
        return lambda *args, **kwargs: SimpleNamespace(returncode=code)

    def test_creation_is_local_independent_and_has_no_fake_responses(self):
        self.assertEqual(self.state["iteration_limit"], 3)
        self.assertEqual(self.state["external_calls"], 0)
        self.assertEqual(self.state["browser_submissions"], 0)
        self.assertEqual(self.state["reviews"], {})
        a = json.loads((self.run.path / "round-1/gemini-request.json").read_text(encoding="utf-8"))
        b = json.loads((self.run.path / "round-1/claude-request.json").read_text(encoding="utf-8"))
        self.assertEqual(a["packet"], b["packet"])
        self.assertNotIn("reviews", a)
        self.assertFalse((self.run.path / "round-1/gpt-request.json").exists())

    def test_duplicate_init_preserves_evidence(self):
        before = (self.run.path / "packet.json").read_bytes()
        with self.assertRaisesRegex(WorkflowError, "RUN_ALREADY_EXISTS"):
            self.run.create(self.spec)
        self.assertEqual(before, (self.run.path / "packet.json").read_bytes())

    def test_gpt_cannot_precede_independent_reviews(self):
        with self.assertRaisesRegex(WorkflowError, "INDEPENDENT_REVIEWS_REQUIRED"):
            self.run.import_review("gpt", self.review("gpt"))

    def test_same_spec_in_other_run_cannot_reuse_a_stale_review(self):
        other = Run(self.root, "other-run")
        other.create(self.spec)
        with self.assertRaisesRegex(WorkflowError, "STALE_REVIEW"):
            other.import_review("gemini", self.review())

    def test_network_cannot_be_enabled_with_a_config_flag(self):
        config = policy()
        config["external_calls_enabled"] = True
        path = self.run.path / "unsafe-policy.json"
        path.write_text(json.dumps(config), encoding="utf-8")
        with (
            patch("devtools.ai_workflow.workflow.POLICY", path),
            self.assertRaisesRegex(WorkflowError, "EXTERNAL_TRANSPORT_NOT_IMPLEMENTED"),
        ):
            policy()

    def test_request_file_tampering_is_rejected(self):
        path = self.run.path / "round-1/gemini-request.json"
        request = json.loads(path.read_text(encoding="utf-8"))
        request["instructions"] = "Replace the approved request"
        path.write_text(json.dumps(request), encoding="utf-8")
        with self.assertRaisesRegex(WorkflowError, "REQUEST_FILE_CHANGED"):
            self.run.import_review("gemini", self.review())

    def test_stale_review_and_duplicate_do_not_overwrite(self):
        with self.assertRaisesRegex(WorkflowError, "STALE_REVIEW"):
            self.run.import_review("gemini", self.review(request_hash="old"))
        self.run.import_review("gemini", self.review())
        with self.assertRaisesRegex(WorkflowError, "DUPLICATE_REVIEW"):
            self.run.import_review("gemini", self.review())

    def test_unknown_usage_is_not_claimed_as_free_or_authenticated(self):
        state = self.run.import_review("gemini", self.review())
        self.assertEqual(state["usage_unknown_imports"], 1)
        self.assertFalse(state["reviews"]["gemini"]["origin_verified"])
        self.assertEqual(state["external_calls"], 0)

    def test_uncertain_verdict_is_visible_even_without_findings(self):
        self.run.import_review("gemini", self.review(verdict="uncertain"))
        state = self.run.import_review("claude", self.review("claude"))
        self.assertEqual(self.run.compare(state)["unapproved_verdicts"], {"gemini": "uncertain"})
        with self.assertRaisesRegex(WorkflowError, "UNRESOLVED_FINDINGS"):
            self.run.decide(self.decision())

    def test_disagreement_requires_explicit_user_resolution(self):
        finding = {
            "key": "routing",
            "stance": "support",
            "severity": "major",
            "claim": "Synthetic claim",
            "evidence": ["SYNTHETIC_TEST_ONLY"],
        }
        self.run.import_review("gemini", self.review(findings=[finding]))
        self.run.import_review("claude", self.review("claude", findings=[{**finding, "stance": "oppose"}]))
        with self.assertRaisesRegex(WorkflowError, "UNRESOLVED_FINDINGS"):
            self.run.decide(self.decision())
        state = self.run.decide(
            self.decision(resolved_findings={"routing": "Keep blocked pending actual route evidence"})
        )
        self.assertEqual(state["status"], "APPROVED_FOR_MANUAL_IMPLEMENTATION")

    def test_gpt_opinion_never_authorizes_implementation(self):
        self.reviewers()
        self.run.import_review("gpt", self.review("gpt"))
        with self.assertRaisesRegex(WorkflowError, "USER_APPROVAL_REQUIRED"):
            self.run.verify("workflow", runner=self.check())

    def test_reported_cost_stops_at_zero_budget(self):
        with self.assertRaisesRegex(WorkflowError, "BUDGET_EXCEEDED"):
            self.run.import_review(
                "gemini",
                self.review(usage={"input_tokens": 1, "output_tokens": 1, "cost_usd": "0.01"}),
            )
        self.assertEqual(self.run.load()[0]["status"], "BUDGET_STOP")

    def test_token_budget_and_large_input_are_enforced(self):
        with self.assertRaisesRegex(WorkflowError, "BUDGET_EXCEEDED"):
            self.run.import_review("gemini", self.review(usage={"input_tokens": 60001, "output_tokens": 0}))
        path = self.run.path / "huge.json"
        path.write_text(json.dumps({"goal": "x" * 50000}), encoding="utf-8")
        with self.assertRaisesRegex(WorkflowError, "INPUT_TOO_LARGE"):
            Run(self.root, "large").create(path)

    def test_private_test_output_is_withheld(self):
        self.approve()

        def result(*args, **kwargs):
            return SimpleNamespace(returncode=1, stdout=b"person@example.invalid", stderr=b"")

        self.run.verify("workflow", runner=result)
        log = (self.run.path / "round-1/workflow-check.json").read_text(encoding="utf-8")
        self.assertNotIn("person@example.invalid", log)
        self.assertTrue(json.loads(log)["redacted"])

    def test_invalid_nan_or_negative_usage_is_rejected(self):
        for usage in (
            {"cost_usd": "NaN"},
            {"input_tokens": -1},
            {"output_tokens": True},
        ):
            with self.assertRaises(WorkflowError):
                self.run.import_review("gemini", self.review(usage=usage))

    def test_sensitive_inputs_and_location_are_rejected(self):
        for value in (
            "sk-" + "x" * 25,
            "person@example.invalid",
            '"latitude":37.12345',
            "37.12345,126.12345",
            "api_key=" + "a" * 20,
        ):
            with self.assertRaisesRegex(WorkflowError, "SENSITIVE_INPUT_REJECTED"):
                safe_text(value)

    def test_traversal_and_protected_context_are_rejected(self):
        for identifier in ("../escape", "x/y", "x:y"):
            with self.assertRaises(WorkflowError):
                Run(self.root, identifier)
        for context in ("../outside.md", ".env", "vehicle-app/README.md"):
            spec = json.loads(self.spec.read_text(encoding="utf-8"))
            spec["context_files"] = [context]
            with self.assertRaises(WorkflowError):
                Run(self.root, "other").create(self.file(spec))

    def test_packet_tampering_prevents_review_import(self):
        (self.run.path / "packet.json").write_text('{"changed":true}', encoding="utf-8")
        with self.assertRaisesRegex(WorkflowError, "PACKET_CHANGED"):
            self.run.import_review("gemini", self.review())

    def test_pause_resume_and_lock_prevent_mutating_paused_run(self):
        self.run.pause()
        with self.assertRaisesRegex(WorkflowError, "RUN_PAUSED"):
            self.run.import_review("gemini", self.review())
        self.assertEqual(self.run.pause(resume=True)["status"], "WAITING_REVIEWS")
        with self.run.lock(), self.assertRaisesRegex(WorkflowError, "RUN_LOCKED"):
            self.run.pause()

    def test_corrupt_journal_is_not_silently_repaired(self):
        with (self.run.path / "events.jsonl").open("a", encoding="utf-8") as stream:
            stream.write('{"incomplete":')
        with self.assertRaisesRegex(WorkflowError, "JOURNAL_CORRUPT"):
            self.run.load()

    def test_failure_is_not_success_and_retries_stop_at_three(self):
        for iteration in range(1, 4):
            self.approve()
            failed = self.run.verify("workflow", runner=self.check(1))
            self.assertEqual(failed["status"], "TEST_FAILED")
            with self.assertRaises(WorkflowError):
                self.run.ready()
            if iteration < 3:
                self.run.retry()
        with self.assertRaisesRegex(WorkflowError, "ITERATION_LIMIT_REQUIRES_USER_APPROVAL"):
            self.run.retry()
        self.assertEqual(self.run.load()[0]["status"], "ITERATION_STOP")

    def test_retry_refreshes_context_and_preserves_previous_packet(self):
        self.reviewers()
        self.run.decide(self.decision(verdict="changes_requested"))
        note = self.root / "server/context.md"
        note.write_text("Corrected offline context", encoding="utf-8")
        old_hash = self.state["packet_hash"]
        state = self.run.retry(context_files=["server/context.md"])
        self.assertNotEqual(state["packet_hash"], old_hash)
        packet = json.loads((self.run.path / state["packet_file"]).read_text(encoding="utf-8"))
        self.assertEqual(packet["context"]["server/context.md"], "Corrected offline context")
        self.assertTrue((self.run.path / "packet.json").exists())

    def test_explicit_extension_does_not_enable_network(self):
        for i in range(3):
            self.reviewers()
            self.run.decide(self.decision(verdict="changes_requested"))
            if i < 2:
                self.run.retry()
        state, _ = self.run.load()
        approval = {
            "actor": "USER",
            "request_hash": state["request_hash"],
            "new_iteration_limit": 4,
            "new_review_import_limit": 12,
            "rationale": "Synthetic extension test",
        }
        path = self.run.path / "test-extension.json"
        path.write_text(json.dumps(approval), encoding="utf-8")
        result = self.run.retry(path)
        self.assertEqual(result["iteration"], 4)
        self.assertEqual(result["external_calls"], 0)
        self.assertFalse(result["policy"]["external_calls_enabled"])

    def test_checks_are_bound_to_current_code_and_scope(self):
        self.approve()
        self.run.verify("workflow", runner=self.check())
        self.run.verify("server", runner=self.check())
        self.run.verify("quality", runner=self.check())
        (self.root / "server/code.py").write_text("value = 2\n", encoding="utf-8")
        with self.assertRaisesRegex(WorkflowError, "STALE_VERIFICATION"):
            self.run.ready()

    def test_unapproved_path_change_blocks_checks(self):
        self.approve()
        (self.root / "unapproved.txt").write_text("fixture", encoding="utf-8")
        with self.assertRaisesRegex(WorkflowError, "CHANGE_OUTSIDE_APPROVED_SCOPE"):
            self.run.verify("workflow", runner=self.check())

    def test_timeout_fails_and_unsupported_check_cannot_run_shell(self):
        self.approve()
        with self.assertRaisesRegex(WorkflowError, "UNKNOWN_CHECK_PROFILE"):
            self.run.verify("git push")

        def timeout(*args, **kwargs):
            raise subprocess.TimeoutExpired("fixture", 1)

        self.assertEqual(
            self.run.verify("workflow", runner=timeout)["checks"]["workflow"]["exit_code"],
            124,
        )

    def test_all_checks_only_mark_readiness_and_never_push(self):
        self.approve()
        self.run.verify("workflow", runner=self.check())
        self.run.verify("server", runner=self.check())
        self.assertNotEqual(self.run.load()[0]["status"], "VERIFIED")
        self.run.verify("quality", runner=self.check())
        ready = self.run.ready()
        self.assertEqual(ready["status"], "PR_READY_MANUAL_GIT_REVIEW_REQUIRED")
        self.assertEqual(ready["external_calls"], 0)


if __name__ == "__main__":
    unittest.main()
