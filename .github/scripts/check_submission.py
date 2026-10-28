"""Check PR artifacts using baseline code and source data, without executing submissions."""

import argparse
import csv
import json
import os
import subprocess
import sys
from pathlib import Path, PurePosixPath

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "verification"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import check_pr_checks  # noqa: E402
from verify_report import (  # noqa: E402
    VerificationError, check_reconciliation, require, safe_file, totals_table, verify,
)

DELIVERABLES = {
    "reports/customer-account-report.csv", "reports/exceptions.csv",
    "verification/review-evidence.md",
}


def allowed(name):
    path = PurePosixPath(name)
    return name in DELIVERABLES or (
        path.parts[0] in {"src", "tests"} and path.suffix == ".py"
    )


def tracked(root):
    result = subprocess.run(
        ["git", "-C", str(root), "ls-files", "-z"], check=True, capture_output=True,
    )
    return set(result.stdout.decode("utf-8").split("\0")) - {""}


def protected_files(baseline, submission):
    for name in sorted(tracked(baseline) | tracked(submission)):
        if not allowed(name):
            original = safe_file(baseline, name)
            current = safe_file(submission, name)
            require(original.read_bytes() == current.read_bytes(),
                    f"Protected file changed: {name}; revert this change in the PR")
    for name in ["src/generate_report.py", "tests/test_generate_report.py"]:
        require(safe_file(submission, name).stat().st_size >= 40,
                f"{name}: provide the implementation/test file")


def check_pr_description(expected):
    if os.environ.get("GITHUB_EVENT_NAME") in {"push", "workflow_dispatch"}:
        body = check_pr_checks.implementation_pull().get("body")
    else:
        event_path = os.environ.get("GITHUB_EVENT_PATH")
        require(bool(event_path), "PR description totals: missing GitHub event payload")
        event = json.loads(Path(event_path).read_text(encoding="utf-8"))
        require(isinstance(event, dict), "PR description totals: invalid GitHub event payload")
        pull = event.get("pull_request")
        require(isinstance(pull, dict), "PR description totals: run this check from a pull request event")
        body = pull.get("body")
    require(isinstance(body, str) and bool(body.strip()),
            "PR description totals: ask Copilot to add the three-total summary table to the pull request description")
    try:
        check_reconciliation(totals_table(body, amount_column="Amount in cents"), expected)
    except VerificationError as error:
        raise VerificationError(f"PR description totals: {error}") from error


def check(baseline, submission, evidence=False, pr_description=False):
    protected_files(baseline, submission)
    result = verify(submission, source_root=baseline, evidence=evidence)
    if pr_description:
        check_pr_description(result)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--submission", type=Path, required=True)
    parser.add_argument("--evidence", action="store_true")
    parser.add_argument("--pr-description", action="store_true",
                        help="Check the PR description totals using the GitHub event payload")
    args = parser.parse_args()
    try:
        result = check(args.baseline, args.submission, args.evidence, args.pr_description)
    except (VerificationError, OSError, csv.Error, UnicodeError, ValueError,
            json.JSONDecodeError, subprocess.CalledProcessError) as error:
        print(f"Submission check failed: {error}", file=sys.stderr)
        return 1
    print("Submission passed: " + json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
