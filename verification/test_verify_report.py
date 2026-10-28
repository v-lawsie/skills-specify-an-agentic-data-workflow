"""Author-side regression coverage; tests use temporary learner copies."""

import csv
import importlib.util
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from verify_report import (
    EXCEPTION_FIELDS, REPORT_FIELDS, VerificationError, expectations, verify,
)

ROOT = Path(__file__).resolve().parents[1]


def load_script(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / ".github/scripts" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


spec_checker = load_script("check_spec")
submission_checker = load_script("check_submission")
completion_checker = load_script("check_pr_checks")
reproduction_checker = load_script("check_reproduction")
feedback_checker = load_script("grade_step")
TOTALS = {"known_net_cents": 22800, "exceptions_net_cents": 2750, "source_net_cents": 25550}
ACCOUNT_EXAMPLES = [
    {"account_id": "A100", "transaction_count": 3, "net_sales_cents": 18000},
    {"account_id": "A200", "transaction_count": 2, "net_sales_cents": 4000},
]
REVIEW_ITEMS = [
    "I compared the results for customers A100 and A200 with my expected results.",
    "I checked the unmatched entries against the original customer list.",
    "I confirmed the three totals reconcile and match my calculations.",
    "I resolved any discrepancies before approving the report.",
]


class ReportFixture(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        shutil.copytree(ROOT / "data", self.root / "data")
        (self.root / "reports").mkdir()
        (self.root / "verification").mkdir()
        (self.root / "specs").mkdir()
        self.write_csv("reports/customer-account-report.csv", REPORT_FIELDS, [
            ["A100", "Retail", "North", 3, 18000],
            ["A200", "Distributor", "West", 2, 4000],
            ["A300", "Retail", "East", 2, 2000],
            ["A400", "Retail", "South", 0, 0],
            ["A500", "Wholesale", "North", 1, -1200],
        ])
        self.write_csv("reports/exceptions.csv", EXCEPTION_FIELDS, [
            ["T009", "X900", "2026-09-30", 3000, "unknown_account"],
            ["T010", "X900", "2026-09-14", -250, "unknown_account"],
        ])
        self.record = {
            "checks": dict.fromkeys(REVIEW_ITEMS, True),
            "decision": "approved",
        }
        self.save_evidence()
        self.write_spec()

    def write_csv(self, relative, header, rows):
        with (self.root / relative).open("w", newline="") as handle:
            writer = csv.writer(handle)
            writer.writerow(header)
            writer.writerows(rows)

    def save_evidence(self):
        lines = ["# My report review", ""]
        for label, checked in self.record["checks"].items():
            lines.append(f"- [{'x' if checked else ' '}] {label}")
        lines.extend(["", "Decision: " + self.record["decision"]])
        (self.root / "verification/review-evidence.md").write_text("\n".join(lines))

    def render_totals(self, totals):
        return (
            "| Check | Expected amount in cents |\n|---|---|\n"
            f"| Known customers | {totals['known_net_cents']} |\n"
            f"| Unmatched customers | {totals['exceptions_net_cents']} |\n"
            f"| All September entries | {totals['source_net_cents']} |\n"
        )

    def replace(self, relative, before, after):
        path = self.root / relative
        path.write_text(path.read_text().replace(before, after))

    def write_spec(self):
        statements = {
            "Purpose": "Finance needs a reliable September customer sales report for its monthly business review.",
            "Audience": "The finance lead and business analyst use the report to verify the monthly sales allocation.",
            "Inputs": "Use data/customer-accounts.csv and data/sales-transactions.csv as the only authoritative synthetic input sources for this exercise.",
            "Outputs": "Write reports/customer-account-report.csv for all accounts and reports/exceptions.csv for all unknown-account September transactions.",
            "Scope": "Include September 2026 net sales in integer USD cents only and exclude payment balances and live connectors.",
            "Human approval": "The business analyst must approve the independently verified results before the implementation pull request is merged.",
            "How to prepare the report": "Use the following agreed rules without inventing business policy during implementation.",
            "Unmatched customers": "Unknown accounts remain visible as exceptions and contribute to source reconciliation.",
            "When to stop": "Stop and ask for clarification when one transaction identifier has two different amounts.",
        }
        text = "\n\n".join(f"## {key}\n\n{value}" for key, value in statements.items())
        text += "\n\n" + "\n\n".join(
            f"**{label}**: The analyst explains this agreed reporting rule in enough detail for a bounded implementation."
            for label in spec_checker.RULES
        )
        text += "\n\n## Expected results\n\n| Account ID | Entry count | Net sales in cents |\n|---|---|---|\n"
        for row in ACCOUNT_EXAMPLES:
            text += f"| {row['account_id']} | {row['transaction_count']} | {row['net_sales_cents']} |\n"
        text += "\n" + self.render_totals(TOTALS)
        (self.root / "specs/report-workflow.md").write_text(text)


class ReportChecks(ReportFixture):
    def test_exact_outputs_and_evidence_pass(self):
        self.assertEqual(verify(self.root, evidence=True), TOTALS)

    def test_oracle_includes_returns_zero_activity_and_boundaries(self):
        expected = expectations(self.root)
        self.assertEqual(expected["reconciliation"], TOTALS)
        self.assertEqual(expected["totals"]["A400"], {"transaction_count": 0, "net_sales_cents": 0})
        self.assertEqual(expected["totals"]["A500"]["net_sales_cents"], -1200)
        self.assertEqual(expected["transaction_ids"]["A100"], ["T001", "T002", "T003"])
        self.assertEqual(expected["transaction_ids"]["A300"], ["T006", "T007"])

    def test_wrong_account_allocation_fails_even_with_balanced_grand_total(self):
        self.replace("reports/customer-account-report.csv", "3,18000", "3,17000")
        self.replace("reports/customer-account-report.csv", "2,4000", "2,5000")
        with self.assertRaises(VerificationError):
            verify(self.root, evidence=True)

    def test_missing_inactive_account_fails(self):
        self.replace("reports/customer-account-report.csv", "A400,Retail,South,0,0\n", "")
        with self.assertRaises(VerificationError):
            verify(self.root)

    def test_account_sort_order_is_required(self):
        path = self.root / "reports/customer-account-report.csv"
        lines = path.read_text().splitlines()
        lines[1], lines[2] = lines[2], lines[1]
        path.write_text("\n".join(lines) + "\n")
        with self.assertRaises(VerificationError):
            verify(self.root)

    def test_report_metadata_and_order_are_checked(self):
        for before, after in [("Retail", "Distributor"), ("3,18000", "4,18000")]:
            with self.subTest(after=after):
                path = self.root / "reports/customer-account-report.csv"
                original = path.read_text()
                path.write_text(original.replace(before, after))
                with self.assertRaises(VerificationError):
                    verify(self.root)
                path.write_text(original)

    def test_unknown_return_cannot_disappear(self):
        self.replace("reports/exceptions.csv", "T010,X900,2026-09-14,-250,unknown_account\n", "")
        with self.assertRaises(VerificationError):
            verify(self.root)

    def test_duplicate_exceptions_fail(self):
        with (self.root / "reports/exceptions.csv").open("a") as handle:
            handle.write("T009,X900,2026-09-30,3000,unknown_account\n")
        with self.assertRaises(VerificationError):
            verify(self.root)

    def test_invalid_source_amounts_fail_including_out_of_period(self):
        for value in ["12.50", "+100", "0100", "-0", ""]:
            with self.subTest(value=value):
                original = (ROOT / "data/sales-transactions.csv").read_text()
                (self.root / "data/sales-transactions.csv").write_text(
                    original.replace("2026-08-31,60000", f"2026-08-31,{value}")
                )
                with self.assertRaises(VerificationError):
                    expectations(self.root)

    def test_conflicting_transaction_fails(self):
        self.replace("data/sales-transactions.csv", "T002,A100,2026-09-12,7500\nT004",
                     "T002,A100,2026-09-12,7501\nT004")
        with self.assertRaisesRegex(VerificationError, "Conflicting"):
            expectations(self.root)

    def test_duplicate_account_fails(self):
        with (self.root / "data/customer-accounts.csv").open("a") as handle:
            handle.write("A100,Retail,North\n")
        with self.assertRaisesRegex(VerificationError, "Duplicate"):
            expectations(self.root)

    def test_bad_date_fails(self):
        for value in ["2026-09-31", "20260901", "2026-9-01"]:
            with self.subTest(value=value):
                original = (ROOT / "data/sales-transactions.csv").read_text()
                (self.root / "data/sales-transactions.csv").write_text(
                    original.replace("2026-09-01", value)
                )
                with self.assertRaises(VerificationError):
                    expectations(self.root)

    def test_bad_header_and_extra_fields_fail(self):
        for content in [
            "account_type,account_id,region\nRetail,A100,North\n",
            "account_id,account_type,region\nA100,Retail,North,extra\n",
        ]:
            with self.subTest(content=content):
                (self.root / "data/customer-accounts.csv").write_text(content)
                with self.assertRaises(VerificationError):
                    expectations(self.root)

    def test_zero_and_empty_exception_output(self):
        (self.root / "data/sales-transactions.csv").write_text(
            "transaction_id,account_id,transaction_date,amount_cents\nT0,A100,2026-09-01,0\n"
        )
        expected = expectations(self.root)
        self.assertEqual(expected["exceptions"], [])
        self.assertEqual(expected["reconciliation"]["source_net_cents"], 0)
        self.assertEqual(expected["totals"]["A100"]["transaction_count"], 1)

    def test_each_review_item_must_be_checked(self):
        for label in REVIEW_ITEMS:
            with self.subTest(label=label):
                self.record["checks"] = dict.fromkeys(REVIEW_ITEMS, True)
                self.record["checks"][label] = False
                self.save_evidence()
                with self.assertRaisesRegex(VerificationError, "Complete this review check"):
                    verify(self.root, evidence=True)

    def test_pending_decision_fails_even_with_completed_checklist(self):
        self.record["decision"] = "pending"
        self.save_evidence()
        with self.assertRaisesRegex(VerificationError, "not approved"):
            verify(self.root, evidence=True)

    def test_review_items_cannot_be_missing_renamed_duplicated_or_malformed(self):
        path = self.root / "verification/review-evidence.md"
        original = path.read_text()
        for label in REVIEW_ITEMS:
            item = f"- [x] {label}"
            for replacement in ["", "- [x] I checked something.", item + "\n" + item,
                                item + "\n" + f"- [ ] {label}", f"- [yes] {label}"]:
                with self.subTest(label=label, replacement=replacement):
                    path.write_text(original.replace(item, replacement))
                    with self.assertRaisesRegex(VerificationError, "Keep exactly one checklist item"):
                        verify(self.root, evidence=True)

    def test_review_accepts_uppercase_x_without_repeated_figures(self):
        self.replace("verification/review-evidence.md", "[x]", "[X]")
        self.assertEqual(verify(self.root, evidence=True), TOTALS)

    def test_review_requires_one_explicit_approval(self):
        path = self.root / "verification/review-evidence.md"
        original = path.read_text()
        for replacement in ["", "Decision: approved\nDecision: pending"]:
            with self.subTest(replacement=replacement):
                path.write_text(original.replace("Decision: approved", replacement))
                with self.assertRaisesRegex(VerificationError, "Keep one Decision"):
                    verify(self.root, evidence=True)

    def test_completing_published_review_template_passes(self):
        text = (ROOT / "verification/review-evidence.md").read_text()
        text = text.replace("- [ ]", "- [x]").replace("Decision: pending", "Decision: approved")
        (self.root / "verification/review-evidence.md").write_text(text)
        self.assertEqual(verify(self.root, evidence=True), TOTALS)

    def test_external_file_symlinks_fail(self):
        path = self.root / "reports/customer-account-report.csv"
        path.unlink()
        path.symlink_to(ROOT / "data/customer-accounts.csv")
        with self.assertRaisesRegex(VerificationError, "symlinks"):
            verify(self.root)

    def test_both_specification_stages_pass(self):
        spec_checker.check(self.root, 1)
        spec_checker.check(self.root, 2)

    def test_specification_does_not_require_repeated_review_prose(self):
        for root in [ROOT, self.root]:
            text = (root / "specs/report-workflow.md").read_text()
            for removed in ["## Checking the totals", "## Checking the finished report",
                            "**Totals check**:", "**Checking the report**:"]:
                self.assertNotIn(removed, text)
        spec_checker.check(self.root, 2)

    def test_concise_clear_answers_do_not_require_a_word_count(self):
        self.replace(
            "specs/report-workflow.md",
            "Finance needs a reliable September customer sales report for its monthly business review.",
            "Report September net sales for Finance.",
        )
        self.replace(
            "specs/report-workflow.md",
            "**Reporting period**: The analyst explains this agreed reporting rule in enough detail for a bounded implementation.",
            "**Reporting period**: Include September 2026 only.",
        )
        spec_checker.check(self.root, 2)
        verify(self.root, evidence=True)

    def test_blank_or_unfinished_answers_still_fail(self):
        for answer in ["", "TODO", "TBD", "done", "<!-- not an answer -->"]:
            with self.subTest(answer=answer), self.assertRaises(VerificationError):
                spec_checker.substantive(answer, "Purpose")

    def test_feedback_identifies_the_actual_problem_and_how_to_retry(self):
        self.replace("specs/report-workflow.md", "| A100 | 3 | 18000 |", "| A100 | 3 | 17000 |")
        feedback = feedback_checker.evaluate(2, ROOT, self.root)
        self.assertFalse(feedback["results_table"][0]["passed"])
        self.assertIn("A100", feedback["tips"][0])
        self.assertIn("net sales in cents", feedback["tips"][0])
        self.assertIn("specs/report-workflow.md", feedback["tips"][1])
        self.assertIn("commit", feedback["tips"][1])

    def test_successful_feedback_uses_lesson_specific_language(self):
        feedback = feedback_checker.evaluate(1, ROOT, self.root)
        self.assertTrue(feedback["results_table"][0]["passed"])
        self.assertIn("report purpose", feedback["results_table"][0]["description"])

    def test_scaffold_fails_both_stages(self):
        shutil.copyfile(ROOT / "specs/report-workflow.md", self.root / "specs/report-workflow.md")
        for stage in [1, 2]:
            with self.subTest(stage=stage), self.assertRaises(VerificationError):
                spec_checker.check(self.root, stage)

    def test_wrong_acceptance_number_fails(self):
        self.replace("specs/report-workflow.md", "| A100 | 3 | 18000 |", "| A100 | 3 | 17000 |")
        with self.assertRaises(VerificationError):
            spec_checker.check(self.root, 2)

    def test_each_expected_total_is_checked(self):
        path = self.root / "specs/report-workflow.md"
        original = path.read_text()
        for name, value in [("Known customers", 22800), ("Unmatched customers", 2750),
                            ("All September entries", 25550)]:
            with self.subTest(name=name):
                path.write_text(original.replace(f"| {name} | {value} |", f"| {name} | {value + 1} |"))
                with self.assertRaisesRegex(VerificationError, "Check the"):
                    spec_checker.check(self.root, 2)

    def test_readable_tables_reject_missing_duplicate_or_malformed_rows(self):
        path = self.root / "specs/report-workflow.md"
        original = path.read_text()
        replacements = [
            ("| A200 | 2 | 4000 |\n", ""),
            ("| A200 | 2 | 4000 |", "| A100 | 3 | 18000 |"),
            ("| Known customers | 22800 |", "| Known customers | TODO |"),
            ("| Unmatched customers | 2750 |", "| Known customers | 2750 |"),
            ("| Account ID | Entry count | Net sales in cents |",
             "| Account ID | Entries | Net sales in cents |"),
            ("| A100 | 3 | 18000 |", "| A100 | 3 | 18,000 |"),
        ]
        for before, after in replacements:
            with self.subTest(after=after):
                path.write_text(original.replace(before, after))
                with self.assertRaises(VerificationError):
                    spec_checker.check(self.root, 2)

    def test_untouched_review_scaffold_does_not_pass(self):
        shutil.copyfile(ROOT / "verification/review-evidence.md",
                        self.root / "verification/review-evidence.md")
        with self.assertRaises(VerificationError):
            verify(self.root, evidence=True)

    def test_missing_rule_label_fails(self):
        self.replace("specs/report-workflow.md", "**Repeated entries**:", "**Different title**:")
        with self.assertRaisesRegex(VerificationError, "Repeated entries"):
            spec_checker.check(self.root, 2)

    def test_first_stage_allows_unfinished_later_sections(self):
        self.replace("specs/report-workflow.md",
                     "Use the following agreed rules without inventing business policy during implementation.",
                     "TODO: complete this in step two")
        spec_checker.check(self.root, 1)
        with self.assertRaises(VerificationError):
            spec_checker.check(self.root, 2)

    def test_submission_uses_baseline_sources_and_blocks_protected_changes(self):
        baseline = self.root / "baseline-copy"
        baseline.mkdir()
        shutil.copytree(self.root / "data", baseline / "data")
        for directory in ["src", "tests"]:
            (self.root / directory).mkdir()
        (self.root / "src/generate_report.py").write_text("# Candidate implementation is not executed by the artifact grader.\n")
        (self.root / "tests/test_generate_report.py").write_text("# Candidate tests are not executed by the artifact grader itself.\n")
        for repo in [baseline, self.root]:
            subprocess.run(["git", "init", "--quiet", str(repo)], check=True)
            subprocess.run(["git", "-C", str(repo), "add", "data"], check=True)
        self.assertEqual(submission_checker.check(baseline, self.root, evidence=True), TOTALS)
        self.replace("data/customer-accounts.csv", "Retail", "Distributor")
        with self.assertRaisesRegex(VerificationError, "Protected file"):
            submission_checker.check(baseline, self.root)

    def test_all_negative_fixtures_fail_independently(self):
        for fixture in (ROOT / "verification/fixtures").glob("*.csv"):
            with self.subTest(fixture=fixture.name):
                target = ("customer-accounts.csv" if fixture.name == "duplicate-accounts.csv"
                          else "sales-transactions.csv")
                original = (self.root / "data" / target).read_text()
                shutil.copyfile(fixture, self.root / "data" / target)
                with self.assertRaises(VerificationError):
                    expectations(self.root)
                (self.root / "data" / target).write_text(original)


class PRDescriptionChecks(ReportFixture):
    def setUp(self):
        super().setUp()
        self.baseline = self.root / "baseline-copy"
        self.baseline.mkdir()
        shutil.copytree(self.root / "data", self.baseline / "data")
        for directory, name in [("src", "generate_report.py"), ("tests", "test_generate_report.py")]:
            (self.root / directory).mkdir()
            (self.root / directory / name).write_text(
                "# Artifact grading inspects this file without executing it.\n"
            )
        for repo in [self.baseline, self.root]:
            subprocess.run(["git", "init", "--quiet", str(repo)], check=True)
            subprocess.run(["git", "-C", str(repo), "add", "data"], check=True)
        self.body = "## Report totals\n\n" + self.render_totals(TOTALS).replace(
            "Expected amount in cents", "Amount in cents"
        )
        self.pull = {
            "body": self.body, "merged_at": "2026-10-28T13:51:50Z",
            "base": {"ref": "main"}, "merge_commit_sha": "merge",
            "head": {"sha": "head", "repo": {"full_name": "learner/exercise"}},
        }
        self.event_path = self.root / "event.json"
        self.set_body(self.body)
        environment = patch.dict("os.environ", {
            "GITHUB_EVENT_PATH": str(self.event_path),
            "GITHUB_EVENT_NAME": "pull_request",
            "GITHUB_REPOSITORY": "learner/exercise",
            "IMPLEMENTATION_PR": "7",
            "GITHUB_SHA": "merge",
        })
        environment.start()
        self.addCleanup(environment.stop)

    def set_body(self, body):
        self.event_path.write_text(json.dumps({"pull_request": {"body": body}}))

    def test_description_totals_and_reports_pass_together(self):
        self.assertEqual(submission_checker.check(
            self.baseline, self.root, evidence=True, pr_description=True,
        ), TOTALS)

    def test_missing_empty_or_incomplete_description_fails(self):
        for body in [None, "", "Reports are ready.", self.body.replace("| Known customers | 22800 |\n", "")]:
            with self.subTest(body=body):
                self.set_body(body)
                with self.assertRaisesRegex(VerificationError, "PR description totals"):
                    submission_checker.check(self.baseline, self.root, pr_description=True)

    def test_each_description_total_is_independently_verified(self):
        for name, value in [("Known customers", 22800), ("Unmatched customers", 2750),
                            ("All September entries", 25550)]:
            with self.subTest(name=name):
                self.set_body(self.body.replace(f"| {name} | {value} |", f"| {name} | {value + 1} |"))
                with self.assertRaisesRegex(VerificationError, "PR description totals: Check the"):
                    submission_checker.check(self.baseline, self.root, pr_description=True)
        self.set_body(self.body.replace("22800", "23000").replace("2750", "2550"))
        with self.assertRaisesRegex(VerificationError, "known-customer total"):
            submission_checker.check(self.baseline, self.root, pr_description=True)

    def test_malformed_or_duplicate_summary_fails(self):
        for body in [
            self.body + "\n" + self.body,
            self.body.replace("| Known customers | 22800 |", "| Known customers | 22,800 |"),
            self.body.replace("| Unmatched customers | 2750 |", "| Known customers | 2750 |"),
            self.body.replace("Amount in cents", "Amount in dollars"),
            self.body.replace("2750", "TODO"),
        ]:
            with self.subTest(body=body):
                self.set_body(body)
                with self.assertRaisesRegex(VerificationError, "PR description totals"):
                    submission_checker.check(self.baseline, self.root, pr_description=True)

    def test_edited_description_recovery_uses_the_new_payload(self):
        self.set_body("Summary missing")
        with self.assertRaises(VerificationError):
            submission_checker.check(self.baseline, self.root, pr_description=True)
        self.event_path.write_text(json.dumps({
            "action": "edited", "pull_request": {"body": self.body},
        }))
        self.assertEqual(submission_checker.check(
            self.baseline, self.root, pr_description=True,
        ), TOTALS)

    def test_lesson_three_reports_missing_totals_and_accepts_correction(self):
        with patch.dict("os.environ", {"GITHUB_EVENT_PATH": str(self.event_path)}):
            self.set_body(None)
            feedback = feedback_checker.evaluate(3, self.baseline, self.root)
            self.assertFalse(feedback["results_table"][0]["passed"])
            self.assertIn("PR description totals", feedback["tips"][0])
            self.set_body(self.body)
            self.assertTrue(feedback_checker.evaluate(3, self.baseline, self.root)["results_table"][0]["passed"])

    def test_lesson_four_requires_totals_before_checking_completion(self):
        self.set_body(None)
        with patch.object(feedback_checker.check_pr_checks, "check") as completion:
            self.assertFalse(feedback_checker.evaluate(4, self.baseline, self.root)["results_table"][0]["passed"])
            completion.assert_not_called()
            self.set_body(self.body)
            self.assertTrue(feedback_checker.evaluate(4, self.baseline, self.root)["results_table"][0]["passed"])
            completion.assert_called_once_with()

    def test_manual_recovery_fetches_the_selected_description(self):
        self.event_path.write_text(json.dumps({"inputs": {"pull-request-number": "7"}}))
        with patch.dict("os.environ", {"GITHUB_EVENT_NAME": "workflow_dispatch"}), patch.object(
            submission_checker.check_pr_checks, "api", return_value=[self.pull],
        ) as api:
            submission_checker.check_pr_description(TOTALS)
            self.assertEqual(api.call_args.args[0],
                             "repos/learner/exercise/pulls/7")

    def test_manual_recovery_still_rejects_bad_totals_and_api_errors(self):
        self.event_path.write_text(json.dumps({"inputs": {"pull-request-number": "7"}}))
        with patch.dict("os.environ", {"GITHUB_EVENT_NAME": "workflow_dispatch"}):
            with patch.object(submission_checker.check_pr_checks, "api", return_value=[
                {**self.pull, "body": self.body.replace("22800", "23000")},
            ]), self.assertRaisesRegex(VerificationError, "PR description totals"):
                submission_checker.check_pr_description(TOTALS)
            with patch.object(submission_checker.check_pr_checks, "api", side_effect=subprocess.CalledProcessError(
                1, ["gh", "api"], stderr="Access denied",
            )), self.assertRaises(subprocess.CalledProcessError):
                submission_checker.check_pr_description(TOTALS)

    def test_manual_recovery_rejects_invalid_pr_number_before_api_call(self):
        with patch.dict("os.environ", {"GITHUB_EVENT_NAME": "workflow_dispatch"}), patch.object(
            submission_checker.check_pr_checks, "api",
        ) as api:
            for number in ["", "0", "not-a-number"]:
                with self.subTest(number=number), patch.dict("os.environ", {"IMPLEMENTATION_PR": number}):
                    self.event_path.write_text(json.dumps({"inputs": {"pull-request-number": number}}))
                    with self.assertRaisesRegex(ValueError, "Select the merged implementation PR"):
                        submission_checker.check_pr_description(TOTALS)
            api.assert_not_called()

    def test_main_push_checks_the_merged_description_not_the_event_body(self):
        self.set_body(None)
        with patch.dict("os.environ", {"GITHUB_EVENT_NAME": "push", "GITHUB_REF": "refs/heads/main"}):
            for body in [self.body, None, self.body.replace("22800", "23000")]:
                with self.subTest(body=body), patch.object(
                    submission_checker.check_pr_checks, "api", return_value=[[{**self.pull, "body": body}]],
                ):
                    if body == self.body:
                        self.assertEqual(submission_checker.check(
                            self.baseline, self.root, evidence=True, pr_description=True,
                        ), TOTALS)
                    else:
                        with self.assertRaisesRegex(VerificationError, "PR description totals"):
                            submission_checker.check(
                                self.baseline, self.root, evidence=True, pr_description=True,
                            )

    def test_final_lesson_completes_from_main_push_with_all_gates(self):
        passing = {
            "id": 1, "name": "Reproduce and test",
            "app": {"slug": "github-actions"}, "conclusion": "success",
        }
        with patch.dict("os.environ", {
            "GITHUB_EVENT_NAME": "push", "GITHUB_REF": "refs/heads/main", "IMPLEMENTATION_PR": "",
        }), patch.object(
            feedback_checker.check_pr_checks, "api",
            side_effect=[[[self.pull]], [[self.pull]], [{"check_runs": [passing]}]],
        ) as api:
            feedback = feedback_checker.evaluate(4, self.baseline, self.root)
            self.assertTrue(feedback["results_table"][0]["passed"], feedback["tips"])
            self.assertEqual(api.call_args_list[-1].args[0],
                             "repos/learner/exercise/commits/head/check-runs?per_page=100")

    def test_final_lesson_from_main_still_requires_analyst_approval(self):
        self.record["decision"] = "pending"
        self.save_evidence()
        with patch.dict("os.environ", {
            "GITHUB_EVENT_NAME": "push", "GITHUB_REF": "refs/heads/main", "IMPLEMENTATION_PR": "",
        }), patch.object(feedback_checker.check_pr_checks, "api") as api:
            feedback = feedback_checker.evaluate(4, self.baseline, self.root)
            self.assertFalse(feedback["results_table"][0]["passed"])
            self.assertIn("Analyst decision is not approved", feedback["tips"][0])
            api.assert_not_called()

    def test_missing_or_invalid_event_payload_fails_explicitly(self):
        with patch.dict("os.environ", {"GITHUB_EVENT_PATH": ""}), self.assertRaisesRegex(
            VerificationError, "missing GitHub event payload",
        ):
            submission_checker.check_pr_description(TOTALS)
        for payload in [[], {}, {"pull_request": None}]:
            with self.subTest(payload=payload):
                self.event_path.write_text(json.dumps(payload))
                with self.assertRaises(VerificationError):
                    submission_checker.check_pr_description(TOTALS)

    def test_actions_submission_entry_point_enforces_summary(self):
        command = [
            sys.executable, "-I", str(ROOT / ".github/scripts/check_submission.py"),
            "--baseline", str(self.baseline), "--submission", str(self.root),
            "--evidence", "--pr-description",
        ]
        result = subprocess.run(command, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.set_body(None)
        result = subprocess.run(command, capture_output=True, text=True)
        self.assertEqual(result.returncode, 1)
        self.assertIn("PR description totals", result.stderr)


class CompletionChecks(unittest.TestCase):
    def setUp(self):
        self.environment = {
            "GITHUB_REPOSITORY": "learner/exercise",
            "IMPLEMENTATION_PR": "7",
            "GITHUB_EVENT_NAME": "pull_request",
            "GITHUB_SHA": "merge",
        }
        self.pull = {
            "merged": True, "merged_at": "2026-10-28T13:51:50Z",
            "base": {"ref": "main"}, "merge_commit_sha": "merge",
            "head": {"sha": "head", "repo": {"full_name": "learner/exercise"}},
        }
        self.passing = {
            "id": 1, "name": "Reproduce and test",
            "app": {"slug": "github-actions"}, "conclusion": "success",
        }

    def run_check(self, runs, pulls=None):
        response = [self.pull]
        if self.environment["GITHUB_EVENT_NAME"] == "push":
            response = [[self.pull] if pulls is None else pulls]
        with patch.dict("os.environ", self.environment), patch.object(
            completion_checker, "api", side_effect=[response, [{"check_runs": runs}]]
        ) as api:
            completion_checker.check()
        return api

    def test_merged_pr_with_passing_reproduction_passes(self):
        self.run_check([self.passing])

    def test_missing_or_newer_failed_reproduction_blocks_completion(self):
        failed = {**self.passing, "id": 2, "conclusion": "failure"}
        for runs in [[], [self.passing, failed]]:
            with self.subTest(runs=runs), self.assertRaises(ValueError):
                self.run_check(runs)

    def test_unmerged_pr_cannot_complete(self):
        self.pull["merged"] = False
        self.pull["merged_at"] = None
        with self.assertRaises(ValueError):
            self.run_check([self.passing])

    def test_manual_recovery_requires_pr_for_current_main(self):
        self.environment["GITHUB_EVENT_NAME"] = "workflow_dispatch"
        self.environment["GITHUB_SHA"] = "different"
        with self.assertRaises(ValueError):
            self.run_check([self.passing])

    def test_main_push_resolves_its_merged_pr_without_manual_input(self):
        self.environment.update({
            "GITHUB_EVENT_NAME": "push", "GITHUB_REF": "refs/heads/main", "IMPLEMENTATION_PR": "",
        })
        api = self.run_check([self.passing])
        self.assertEqual(api.call_args_list[0].args[0],
                         "repos/learner/exercise/commits/merge/pulls?per_page=100")
        self.assertEqual(api.call_args_list[1].args[0],
                         "repos/learner/exercise/commits/head/check-runs?per_page=100")

    def test_main_push_requires_one_matching_merged_pr(self):
        self.environment.update({
            "GITHUB_EVENT_NAME": "push", "GITHUB_REF": "refs/heads/main", "IMPLEMENTATION_PR": "",
        })
        for pulls in [[], [{**self.pull, "merge_commit_sha": "other"}],
                      [{**self.pull, "merged_at": None}], [self.pull, self.pull]]:
            with self.subTest(pulls=pulls), self.assertRaisesRegex(ValueError, "exactly one merged"):
                self.run_check([self.passing], pulls)

    def test_main_push_still_requires_same_repository_and_main_base(self):
        self.environment.update({
            "GITHUB_EVENT_NAME": "push", "GITHUB_REF": "refs/heads/main", "IMPLEMENTATION_PR": "",
        })
        for pull in [
            {**self.pull, "base": {"ref": "other"}},
            {**self.pull, "head": {"sha": "head", "repo": None}},
            {**self.pull, "head": {"sha": "head", "repo": {"full_name": "other/repository"}}},
        ]:
            with self.subTest(pull=pull), self.assertRaisesRegex(ValueError, "same-repository"):
                self.run_check([self.passing], [pull])

    def test_main_push_still_requires_successful_latest_head_reproduction(self):
        self.environment.update({
            "GITHUB_EVENT_NAME": "push", "GITHUB_REF": "refs/heads/main", "IMPLEMENTATION_PR": "",
        })
        failed = {**self.passing, "id": 2, "conclusion": "failure"}
        for runs in [[], [self.passing, failed]]:
            with self.subTest(runs=runs), self.assertRaisesRegex(ValueError, "Reproduce and test"):
                self.run_check(runs)

    def test_pushes_outside_main_cannot_complete(self):
        self.environment.update({
            "GITHUB_EVENT_NAME": "push", "GITHUB_REF": "refs/heads/feature", "IMPLEMENTATION_PR": "",
        })
        with self.assertRaisesRegex(ValueError, "main"):
            self.run_check([self.passing])


class ReproductionChecks(ReportFixture):
    def setUp(self):
        super().setUp()
        (self.root / "src").mkdir()
        (self.root / "tests").mkdir()
        self.program = f"""
import csv
import sys
from pathlib import Path
sys.path.insert(0, {str(ROOT / "verification")!r})
from verify_report import expectations, VerificationError, REPORT_FIELDS, EXCEPTION_FIELDS
try:
    expected = expectations(Path.cwd())
except VerificationError as error:
    print(error, file=sys.stderr)
    sys.exit(1)
Path("reports").mkdir(exist_ok=True)
for filename, fields, rows in [
    ("customer-account-report.csv", REPORT_FIELDS, expected["report"]),
    ("exceptions.csv", EXCEPTION_FIELDS, expected["exceptions"]),
]:
    with (Path("reports") / filename).open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
"""
        (self.root / "src/generate_report.py").write_text(self.program)
        (self.root / "tests/test_generate_report.py").write_text(
            "import unittest\nclass SmokeTest(unittest.TestCase):\n"
            "    def test_something(self):\n        self.assertTrue(True)\n"
        )

    def test_fresh_reports_repeated_runs_tests_and_bad_inputs_pass(self):
        reproduction_checker.check(ROOT, self.root)

    def test_no_op_program_cannot_pass_using_committed_reports(self):
        (self.root / "src/generate_report.py").write_text("# Does not create any report.\n")
        with self.assertRaisesRegex(VerificationError, "Missing required file"):
            reproduction_checker.check(ROOT, self.root)

    def test_empty_test_suite_fails(self):
        (self.root / "tests/test_generate_report.py").write_text("# No tests.\n")
        with self.assertRaisesRegex(VerificationError, "No tests were found"):
            reproduction_checker.check(ROOT, self.root)

    def test_ignoring_bad_inputs_fails(self):
        (self.root / "src/generate_report.py").write_text(
            self.program.replace("expectations(Path.cwd())", f"expectations({str(ROOT)!r})")
        )
        with self.assertRaisesRegex(VerificationError, "must stop on this invalid input"):
            reproduction_checker.check(ROOT, self.root)

    def test_changed_sources_fail(self):
        (self.root / "src/generate_report.py").write_text(
            self.program + '\nPath("data/customer-accounts.csv").write_text("changed")\n'
        )
        with self.assertRaisesRegex(VerificationError, "changed the original source"):
            reproduction_checker.check(ROOT, self.root)

    def test_partial_reports_on_error_fail(self):
        (self.root / "src/generate_report.py").write_text(
            self.program.replace(
                "print(error, file=sys.stderr)",
                'Path("reports").mkdir(exist_ok=True)\n'
                '    Path("reports/exceptions.csv").write_text("partial")\n'
                "    print(error, file=sys.stderr)",
            )
        )
        with self.assertRaisesRegex(VerificationError, "left a partial report"):
            reproduction_checker.check(ROOT, self.root)


if __name__ == "__main__":
    unittest.main()
