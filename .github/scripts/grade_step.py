"""Turn a trusted grading result into specific, lesson-level feedback."""

import argparse
import csv
import html
import json
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import check_pr_checks  # noqa: E402
import check_spec  # noqa: E402
import check_submission  # noqa: E402
from verify_report import VerificationError  # noqa: E402

DESCRIPTIONS = {
    1: "Your report purpose, source files, outputs, and approval decision",
    2: "Your reporting rules, customer examples, and totals",
    3: "Copilot's customer report, unmatched entries, and PR description totals",
    4: "Your completed review checklist, PR description totals, approval, and accepted work",
}
NEXT_ACTIONS = {
    1: "Edit the named section in specs/report-workflow.md on main and commit your correction.",
    2: "Correct the named rule or table in specs/report-workflow.md on main, then commit again.",
    3: "Ask @copilot in the implementation pull request to correct the named report, file, or description totals; checks rerun when the PR description or commits change.",
    4: "Complete the review checklist and approval yourself, or ask Copilot to correct the reports or description totals. After a correction, run Step 4 on main using the merged PR's number; merge report corrections first.",
}


def evaluate(stage, baseline, submission):
    try:
        if stage in (1, 2):
            check_spec.check(submission, stage)
        else:
            check_submission.check(baseline, submission, evidence=(stage == 4), pr_description=True)
            if stage == 4:
                check_pr_checks.check()
    except (VerificationError, OSError, csv.Error, UnicodeError, ValueError,
            subprocess.CalledProcessError) as error:
        message = str(error)
        if isinstance(error, subprocess.CalledProcessError) and error.stderr:
            message += ": " + error.stderr
        message = html.escape(" ".join(message.split())[:2000])
        return {
            "step_number": stage,
            "results_table": [{"description": DESCRIPTIONS[stage], "passed": False}],
            "tips": [message, NEXT_ACTIONS[stage]],
        }
    return {
        "step_number": stage,
        "results_table": [{"description": DESCRIPTIONS[stage], "passed": True}],
        "tips": ["This check supports your review; it does not replace reading your instructions or checking the figures yourself."],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stage", type=int, choices=[1, 2, 3, 4], required=True)
    args = parser.parse_args()
    feedback = evaluate(args.stage, Path("baseline"), Path("submission"))
    if "GITHUB_OUTPUT" in os.environ:
        with Path(os.environ["GITHUB_OUTPUT"]).open("a") as output:
            output.write("feedback_vars=" + json.dumps(feedback) + "\n")
    for tip in feedback["tips"]:
        print(tip)
    return 0 if feedback["results_table"][0]["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
