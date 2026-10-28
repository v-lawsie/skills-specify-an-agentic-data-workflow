"""Check specification structure and source-derived acceptance examples."""

import argparse
import csv
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "verification"))
from verify_report import (  # noqa: E402
    VerificationError, account_table, check_accounts, check_reconciliation,
    expectations, require, require_written_text, safe_file, totals_table,
)

BASIC = ["Purpose", "Audience", "Inputs", "Outputs", "Scope", "Human approval"]
ADVANCED = ["How to prepare the report", "Unmatched customers", "When to stop"]
RULES = ["Reporting period", "Sales and returns", "Customers", "Repeated entries",
         "Unmatched entries", "Problems with the files"]


def sections(text):
    matches = list(re.finditer(r"^## (.+)$", text, re.MULTILINE))
    result = {}
    for index, match in enumerate(matches):
        name = match.group(1).strip()
        require(name not in result, f"Duplicate specification heading: {name}")
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        result[name] = text[match.end():end].strip()
    return result


def substantive(text, context):
    prose = re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL).strip()
    require_written_text(prose, context)


def check(root, stage):
    text = safe_file(root, "specs/report-workflow.md").read_text(encoding="utf-8")
    parts = sections(text)
    for name in BASIC + (ADVANCED if stage == 2 else []):
        require(name in parts, f"Keep the ## {name} heading")
        substantive(parts[name], name)
    for path in ["data/customer-accounts.csv", "data/sales-transactions.csv"]:
        require(path in parts["Inputs"], f"Inputs must reference {path}")
    for path in ["reports/customer-account-report.csv", "reports/exceptions.csv"]:
        require(path in parts["Outputs"], f"Outputs must reference {path}")
    approval = parts["Human approval"].lower()
    require("analyst" in approval and "approv" in approval
            and "before" in approval and "merg" in approval,
            "State that the analyst approves before merge")
    if stage == 1:
        return
    for label in RULES:
        rule = re.search(rf"^\*\*{label}\*\*:\s*(.+)$", text, re.MULTILINE)
        require(rule is not None, f"Keep the **{label}**: rule label")
        substantive(rule.group(1), f"Rule {label}")
    require("Expected results" in parts, "Keep ## Expected results")
    expected = expectations(root)
    check_accounts(account_table(parts["Expected results"]), expected)
    check_reconciliation(totals_table(parts["Expected results"]), expected["reconciliation"])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--stage", type=int, choices=[1, 2], required=True)
    args = parser.parse_args()
    try:
        check(args.root, args.stage)
    except (VerificationError, OSError, csv.Error, UnicodeError, json.JSONDecodeError) as error:
        print(f"Specification check failed: {error}", file=sys.stderr)
        return 1
    print("Specification structure passed; prose still requires human judgment.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
