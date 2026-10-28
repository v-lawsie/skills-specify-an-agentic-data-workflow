"""Exercise learner code only in disposable copies with no existing reports."""

import argparse
import csv
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "verification"))
from verify_report import VerificationError, require, safe_file, verify  # noqa: E402

REPORTS = ["reports/customer-account-report.csv", "reports/exceptions.csv"]
TEST_RUNNER = """
import sys
import unittest
suite = unittest.defaultTestLoader.discover("tests")
if suite.countTestCases() == 0:
    sys.exit("No tests were found. Add runnable tests for the reporting rules.")
result = unittest.TextTestRunner(verbosity=2).run(suite)
sys.exit(0 if result.wasSuccessful() else 1)
"""


def prepare(baseline, submission, work):
    (work / "data").mkdir()
    for filename in ["customer-accounts.csv", "sales-transactions.csv"]:
        shutil.copyfile(safe_file(baseline, "data/" + filename), work / "data" / filename)
    fixtures = work / "verification/fixtures"
    fixtures.mkdir(parents=True)
    for filename in ["invalid-amount.csv", "conflicting-transactions.csv", "duplicate-accounts.csv"]:
        shutil.copyfile(safe_file(baseline, "verification/fixtures/" + filename), fixtures / filename)
    for directory in ["src", "tests"]:
        (work / directory).mkdir()
        for path in (submission / directory).rglob("*.py"):
            relative = path.relative_to(submission)
            source = safe_file(submission, relative)
            destination = work / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, destination)


def execute(work, command):
    try:
        return subprocess.run(
            [sys.executable, *command], cwd=work, capture_output=True,
            text=True, timeout=60,
        )
    except subprocess.TimeoutExpired as error:
        raise VerificationError("The program or tests took longer than 60 seconds. Ask Copilot to investigate.") from error


def require_success(result, context):
    detail = (result.stderr or result.stdout).strip()
    require(result.returncode == 0, f"{context} failed. {detail}")


def source_snapshot(work):
    return {
        name: safe_file(work, "data/" + name).read_bytes()
        for name in ["customer-accounts.csv", "sales-transactions.csv"]
    }


def check(baseline, submission):
    baseline, submission = Path(baseline), Path(submission)
    with tempfile.TemporaryDirectory() as temporary:
        work = Path(temporary)
        prepare(baseline, submission, work)
        original_sources = source_snapshot(work)
        require_success(execute(work, ["src/generate_report.py"]), "Creating reports from scratch")
        require(source_snapshot(work) == original_sources, "The program changed the original source files")
        verify(work, source_root=baseline)
        generated = {name: safe_file(work, name).read_bytes() for name in REPORTS}
        for name in REPORTS:
            require(generated[name] == safe_file(submission, name).read_bytes(),
                    f"{name}: the freshly generated file differs from the report in the pull request")
        require_success(execute(work, ["src/generate_report.py"]), "Repeating report generation")
        require(all(safe_file(work, name).read_bytes() == content for name, content in generated.items()),
                "Running the program twice changed the reports")
        require(source_snapshot(work) == original_sources, "The program changed the original source files")

    with tempfile.TemporaryDirectory() as temporary:
        work = Path(temporary)
        prepare(baseline, submission, work)
        require_success(execute(work, ["-c", TEST_RUNNER]), "Checking the implementation tests")

    cases = [
        ("invalid-amount.csv", "sales-transactions.csv"),
        ("conflicting-transactions.csv", "sales-transactions.csv"),
        ("duplicate-accounts.csv", "customer-accounts.csv"),
    ]
    for fixture, target in cases:
        with tempfile.TemporaryDirectory() as temporary:
            work = Path(temporary)
            prepare(baseline, submission, work)
            shutil.copyfile(safe_file(baseline, "verification/fixtures/" + fixture),
                            work / "data" / target)
            original_sources = source_snapshot(work)
            result = execute(work, ["src/generate_report.py"])
            require(result.returncode != 0, f"{fixture}: the program must stop on this invalid input, not report success")
            require(bool((result.stderr + result.stdout).strip()),
                    f"{fixture}: explain why processing stopped")
            require(not any((work / name).exists() for name in REPORTS),
                    f"{fixture}: processing stopped but left a partial report")
            require(source_snapshot(work) == original_sources,
                    f"{fixture}: the program changed the source files")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--submission", type=Path, required=True)
    args = parser.parse_args()
    try:
        check(args.baseline, args.submission)
    except (VerificationError, OSError, csv.Error, UnicodeError, json.JSONDecodeError) as error:
        print(f"Report reproduction failed: {error}", file=sys.stderr)
        return 1
    print("Fresh reports match, repeat runs agree, tests ran, and all three invalid-input cases stopped correctly.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
