"""Check authoring structure. Deliberately fail for unresolved publication placeholders."""

import re
import sys
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import yaml

ROOT = Path(__file__).resolve().parents[2]
TITLE = "Specify an Agentic Data Workflow"
NAME = "specify-an-agentic-data-workflow"


def validate():
    errors = []

    def check(condition, message):
        if not condition:
            errors.append(message)

    readme = (ROOT / "README.md").read_text()
    files = [ROOT / "README.md"] + sorted((ROOT / ".github").rglob("*"))
    placeholders = re.compile(
        r"replace-me|\b(?:OWNER|REPO|ORG|TITLE|FEATURE|VISIBILITY)\b"
        r"|\[(?:Step name|Action|Exercise title|Theory title|Activity title)\]"
    )
    for path in files:
        if path.is_file() and path.suffix in {".md", ".yml", ".yaml"}:
            for number, line in enumerate(path.read_text().splitlines(), 1):
                if placeholders.search(line):
                    errors.append(f"{path.relative_to(ROOT)}:{number}: unresolved publication placeholder")

    check(readme.startswith("# " + TITLE + "\n"), "README title differs from approved title")
    badges = re.findall(r"\[!\[\]\((https://img.shields.io/badge/Copy[^)]+)\)\]\(([^)]+)\)", readme)
    check(len(badges) == 1, "README must contain exactly one canonical Copy Exercise badge")
    if len(badges) == 1:
        image, url = badges[0]
        check(image == "https://img.shields.io/badge/Copy%20Exercise-%E2%86%92-1f883d?style=for-the-badge&logo=github&labelColor=197935",
              "Copy Exercise badge image was altered")
        parsed = urlparse(url)
        query = parse_qs(parsed.query)
        check(parsed.scheme == "https" and parsed.netloc == "github.com" and parsed.path == "/new",
              "Badge must link to github.com/new")
        for key, value in {"template_name": NAME, "name": "skills-" + NAME,
                           "owner": "@me", "description": "Exercise: " + TITLE,
                           "visibility": "public"}.items():
            check(query.get(key) == [value], f"Badge {key} mismatch")
        check("### How to start this exercise" in readme[:readme.index("[![]")],
              "Badge must follow the start heading")
    license_path = ROOT / "LICENSE"
    check(license_path.is_file(), "LICENSE missing: copyright holder remains undecided")
    check(readme.rstrip().split("\n")[-3] == "---", "README must end with the canonical footer rule")
    check(readme.rstrip().split("\n")[-1].startswith("&copy; 2026 "),
          "README footer year/format mismatch")
    if license_path.is_file():
        check("Copyright (c) 2026 " in license_path.read_text(), "License year must match README")

    flows = {}
    for path in sorted((ROOT / ".github/workflows").glob("*.yml")):
        flow = yaml.load(path.read_text(), Loader=yaml.BaseLoader)
        flows[path.name] = flow
        check(flow.get("permissions") == {}, f"{path.name}: workflow permissions must be empty")
        check("on" in flow and isinstance(flow["on"], dict), f"{path.name}: missing real trigger")
        jobs = flow.get("jobs", {})
        if path.name in {"1-step.yml", "2-step.yml"}:
            condition = jobs.get("find_exercise", {}).get("if", "")
            check("(github.event_name != 'push' || github.event.created == false)" in condition,
                  f"{path.name}: skip the initial branch-creation push before the lesson issue exists")
        for name, job in jobs.items():
            check("permissions" in job, f"{path.name}/{name}: declare per-job permissions")
            if path.name == "check-report.yml":
                check(job.get("if") == "!github.event.repository.is_template",
                      f"{path.name}/{name}: run learner grading only outside the exercise template")
        if "check_step_work" in jobs:
            check_job = jobs["check_step_work"]
            check(check_job.get("permissions", {}).get("contents") != "write"
                  and check_job.get("permissions", {}).get("actions") != "write",
                  f"{path.name}: grading must not have contents/actions write")
            post = jobs.get("post_next_step_content", jobs.get("post_review_content", {}))
            check("check_step_work" in post.get("needs", []), f"{path.name}: grading does not gate progression")
        for key, value in flow.get("env", {}).items():
            if re.fullmatch(r"STEP_\d+_FILE|REVIEW_FILE", key):
                check((ROOT / value).is_file(), f"{path.name}: missing {value}")

    final = flows.get("4-step.yml", {})
    triggers = final.get("on", {})
    check("pull_request" not in triggers, "Step 4: finish from main, not a Copilot PR approval gate")
    check(triggers.get("push", {}).get("branches") == ["main"],
          "Step 4: completion must trigger on pushes to main")
    check(set(triggers.get("push", {}).get("paths", [])) ==
          {"src/**", "tests/**", "reports/**", "verification/review-evidence.md"},
          "Step 4: scope completion pushes to implementation and review files")
    final_jobs = final.get("jobs", {})
    check("github.event.created == false" in final_jobs.get("find_exercise", {}).get("if", ""),
          "Step 4: skip initial branch-creation pushes")
    check(final_jobs.get("check_step_work", {}).get("permissions", {}).get("pull-requests") == "read",
          "Step 4: grading needs pull-requests read to inspect the merged PR")

    check(set(flows) >= {"0-start-exercise.yml", "check-report.yml"},
          "Missing start or unprivileged report workflow")
    for number in range(1, 5):
        path = ROOT / f".github/steps/{number}-step.md"
        check(path.is_file(), f"Missing step {number} content")
        flow = flows.get(f"{number}-step.yml", {})
        check(flow.get("name") == f"Step {number}", f"Step {number} workflow name mismatch")
        if not path.is_file():
            continue
        text = path.read_text()
        check(text.startswith(f"## Step {number}: "), f"Step {number} opening heading mismatch")
        check(text.count("### 📖 Theory:") == 1, f"Step {number} must have one Theory")
        activities = list(re.finditer(r"^### ⌨️ Activity(?:( \d+))?: .+$", text, re.MULTILINE))
        check(bool(activities), f"Step {number} needs an Activity")
        for index, activity in enumerate(activities):
            suffix = activity.group(1)
            expected = None if len(activities) == 1 else f" {index + 1}"
            check(suffix == expected, f"Step {number}: activity numbering mismatch")
            end = activities[index + 1].start() if index + 1 < len(activities) else len(text)
            block = text[activity.end():end]
            check(block.count("<summary>Having trouble? 🤷</summary>") == 1,
                  f"Step {number} activity {index + 1}: missing recovery block")
            instructions = block.split("<details>", 1)[0].strip()
            check(instructions.startswith("1. "), f"Step {number}: instructions must be numbered")
            check(all(not line or line.startswith(("1. ", "   "))
                      for line in instructions.splitlines()), f"Step {number}: split instruction list")
            if index == len(activities) - 1:
                final_instruction = (
                    "1. Wait a moment for Mona to check your work, confirm completion, and share the exercise recap."
                    if number == 4 else
                    "1. Wait a moment for Mona to check your work, provide feedback, and share the next lesson."
                )
                check(instructions.endswith(final_instruction),
                      f"Step {number}: missing final Mona instruction")
        check(not re.search(r"\{\{|\{%", text), f"Step {number}: unexpected template variables")
        headings = re.findall(r"^### (.+)$", text, re.MULTILINE)
        check(all(heading.startswith(("📖 Theory:", "⌨️ Activity")) for heading in headings),
              f"Step {number}: unexpected third-level heading")
        raw_flow = (ROOT / f".github/workflows/{number}-step.yml").read_text()
        check(("# Last step of the exercise" in raw_flow) == (number == 4),
              f"Step {number}: final workflow marker mismatch")

    review = ROOT / ".github/steps/x-review.md"
    check(review.is_file() and review.read_text().startswith("## Review\n"), "Missing review skeleton")
    all_yaml = sorted((ROOT / ".github").rglob("*.yml"))
    for path in all_yaml:
        yaml.load(path.read_text(), Loader=yaml.BaseLoader)
        text = path.read_text()
        for ref in re.findall(r"skills/exercise-toolkit/[^\s@]+@([^\s]+)", text):
            check(ref == "v0.9.3", f"{path.name}: mixed toolkit pin")
        if "repository: skills/exercise-toolkit" in text:
            check("ref: v0.9.3" in text, f"{path.name}: unpinned toolkit checkout")
        check("pull_request_target" not in text, f"{path.name}: privileged PR trigger not allowed")
    return errors


if __name__ == "__main__":
    problems = validate()
    if problems:
        print("\n".join(problems), file=sys.stderr)
        sys.exit(1)
    print("Exercise structure passed; live fresh-copy validation remains a separate gate.")
