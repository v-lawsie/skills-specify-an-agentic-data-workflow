"""Require successful unprivileged reproduction on the merged PR's exact head."""

import json
import os
import subprocess
import sys


def api(path):
    result = subprocess.run(
        ["gh", "api", "--paginate", "--slurp", path],
        check=True, capture_output=True, text=True,
    )
    return json.loads(result.stdout)


def implementation_pull():
    repository = os.environ["GITHUB_REPOSITORY"]
    if os.environ["GITHUB_EVENT_NAME"] == "push":
        if os.environ.get("GITHUB_REF") != "refs/heads/main":
            raise ValueError("Completion must run on main")
        sha = os.environ["GITHUB_SHA"]
        pages = api(f"repos/{repository}/commits/{sha}/pulls?per_page=100")
        matches = [
            pull for page in pages for pull in page
            if pull["merged_at"] and pull["merge_commit_sha"] == sha
        ]
        if len(matches) != 1:
            raise ValueError("Completion requires exactly one merged implementation PR for this main commit")
        return matches[0]
    number = os.environ.get("IMPLEMENTATION_PR", "")
    if not number.isdigit() or int(number) < 1:
        raise ValueError("Select the merged implementation PR number for manual recovery")
    return api(f"repos/{repository}/pulls/{number}")[0]


def check():
    repository = os.environ["GITHUB_REPOSITORY"]
    pull = implementation_pull()
    if not (pull["merged_at"] and pull["base"]["ref"] == "main"
            and pull["head"]["repo"]
            and pull["head"]["repo"]["full_name"] == repository):
        raise ValueError("Completion requires a merged same-repository implementation PR into main")
    if os.environ["GITHUB_EVENT_NAME"] == "workflow_dispatch":
        if pull["merge_commit_sha"] != os.environ["GITHUB_SHA"]:
            raise ValueError("For manual recovery, select the PR that produced current main")
    pages = api(f"repos/{repository}/commits/{pull['head']['sha']}/check-runs?per_page=100")
    runs = [
        run for page in pages for run in page["check_runs"]
        if run["name"] == "Reproduce and test" and run["app"]["slug"] == "github-actions"
    ]
    if not runs or max(runs, key=lambda run: run["id"])["conclusion"] != "success":
        raise ValueError("Reproduce and test must pass on the PR's latest head before completion; rerun Step 4 after it passes")
    print("Merged implementation PR and successful reproduction check confirmed.")


if __name__ == "__main__":
    try:
        check()
    except (ValueError, KeyError, subprocess.CalledProcessError) as error:
        print(f"Completion check failed: {error}", file=sys.stderr)
        sys.exit(1)
