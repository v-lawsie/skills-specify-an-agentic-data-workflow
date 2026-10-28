"""Independent source-to-report checks; never imports learner implementation."""

import argparse
import csv
import json
import re
import sys
from datetime import date
from pathlib import Path

ACCOUNT_FIELDS = ["account_id", "account_type", "region"]
TRANSACTION_FIELDS = [
    "transaction_id", "account_id", "transaction_date", "amount_cents"
]
REPORT_FIELDS = ACCOUNT_FIELDS + ["transaction_count", "net_sales_cents"]
EXCEPTION_FIELDS = TRANSACTION_FIELDS + ["reason"]
INTEGER = re.compile(r"(?:0|-?[1-9][0-9]*)\Z")
REVIEW_CHECKS = [
    "I compared the results for customers A100 and A200 with my expected results.",
    "I checked the unmatched entries against the original customer list.",
    "I confirmed the three totals reconcile and match my calculations.",
    "I resolved any discrepancies before approving the report.",
]


class VerificationError(ValueError):
    """A source, report, or review record violates the published contract."""


def require(condition, message):
    if not condition:
        raise VerificationError(message)


def require_written_text(text, context):
    require(bool(re.search(r"[A-Za-z0-9]", text)),
            f"{context}: write your answer rather than leaving this blank")
    require(not re.search(r"\b(?:TODO|TBD)\b", text, re.IGNORECASE)
            and text.strip().lower() not in {"done", "n/a", "none", "pending", "yes", "no"},
            f"{context}: replace the unfinished answer with your own explanation")


def safe_file(root, relative):
    root = Path(root).resolve()
    path = root / relative
    require(not path.is_symlink(), f"{relative}: symlinks are not allowed")
    require(path.resolve().is_relative_to(root), f"{relative}: path escapes repository")
    require(path.is_file(), f"Missing required file: {relative}")
    require(path.stat().st_size <= 1_000_000, f"{relative}: exceeds exercise size limit")
    return path


def read_csv(root, relative, fields):
    path = safe_file(root, relative)
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle, strict=True)
        require(reader.fieldnames == fields, f"{relative}: expected header {','.join(fields)}")
        rows = []
        for number, row in enumerate(reader, 2):
            require(set(row) == set(fields), f"{relative}:{number}: wrong field count")
            require(
                all(isinstance(value, str) and value and value == value.strip()
                    for value in row.values()),
                f"{relative}:{number}: fields must be nonempty and unpadded",
            )
            rows.append(row)
    return rows


def integer(value, context):
    require(
        isinstance(value, str) and INTEGER.fullmatch(value) is not None,
        f"{context}: expected canonical integer cents/count",
    )
    return int(value)


def expectations(root):
    accounts = read_csv(root, "data/customer-accounts.csv", ACCOUNT_FIELDS)
    account_map = {}
    totals = {}
    ids = {}
    for row in accounts:
        key = row["account_id"]
        require(key not in account_map, f"Duplicate account_id: {key}")
        account_map[key] = row
        totals[key] = {"transaction_count": 0, "net_sales_cents": 0}
        ids[key] = []

    transactions = {}
    for row in read_csv(root, "data/sales-transactions.csv", TRANSACTION_FIELDS):
        key = row["transaction_id"]
        integer(row["amount_cents"], f"Transaction {key}")
        raw_date = row["transaction_date"]
        try:
            parsed_date = date.fromisoformat(raw_date)
        except ValueError as error:
            raise VerificationError(f"Transaction {key}: invalid date {raw_date}") from error
        require(parsed_date.isoformat() == raw_date, f"Transaction {key}: use YYYY-MM-DD")
        require(
            key not in transactions or transactions[key] == row,
            f"Conflicting transaction_id: {key}",
        )
        transactions[key] = row

    source_net = 0
    exceptions = []
    for key, row in sorted(transactions.items()):
        if not "2026-09-01" <= row["transaction_date"] <= "2026-09-30":
            continue
        amount = int(row["amount_cents"])
        source_net += amount
        account = row["account_id"]
        if account in totals:
            totals[account]["transaction_count"] += 1
            totals[account]["net_sales_cents"] += amount
            ids[account].append(key)
        else:
            exceptions.append({**row, "reason": "unknown_account"})

    report = [
        {**account_map[key], **{name: str(value) for name, value in totals[key].items()}}
        for key in sorted(account_map)
    ]
    reconciliation = {
        "known_net_cents": sum(row["net_sales_cents"] for row in totals.values()),
        "exceptions_net_cents": sum(int(row["amount_cents"]) for row in exceptions),
        "source_net_cents": source_net,
    }
    return {
        "report": report, "exceptions": exceptions, "totals": totals,
        "transaction_ids": ids, "reconciliation": reconciliation,
    }


def check_accounts(examples, expected):
    require(isinstance(examples, list) and len(examples) >= 2,
            "Provide at least two distinct account examples")
    seen = set()
    for example in examples:
        require(isinstance(example, dict), "Each account example must be an object")
        key = example.get("account_id")
        require(isinstance(key, str) and key in expected["totals"],
                f"Unknown example account: {key}")
        require(key not in seen, f"Repeated example account: {key}")
        seen.add(key)
        for field in ("transaction_count", "net_sales_cents"):
            value = example.get(field)
            label = "entry count" if field == "transaction_count" else "net sales in cents"
            require(type(value) is int and value == expected["totals"][key][field],
                    f"{key}: check the {label} against its unique September entries")


def check_reconciliation(actual, expected):
    require(isinstance(actual, dict), "Provide a reconciliation object")
    require(set(actual) == set(expected), "Reconciliation must contain exactly the three totals")
    for key, value in expected.items():
        label = {
            "known_net_cents": "known-customer total",
            "exceptions_net_cents": "unmatched-customer total",
            "source_net_cents": "total of all September entries",
        }[key]
        require(type(actual.get(key)) is int and actual[key] == value,
                f"Check the {label}: add September amounts in cents, keeping returns negative and counting repeated entries once")
    require(actual["known_net_cents"] + actual["exceptions_net_cents"] == actual["source_net_cents"],
            "Reconciliation equation does not balance")


def markdown_table(text, headers):
    tables = []
    current = []
    for line in text.splitlines() + [""]:
        if line.strip().startswith("|"):
            cells = [cell.strip().strip("`") for cell in line.strip().strip("|").split("|")]
            current.append(cells)
        elif current:
            if current[0] == headers:
                tables.append(current)
            current = []
    require(len(tables) == 1, f"Keep exactly one table with columns: {' | '.join(headers)}")
    table = tables[0]
    require(len(table) >= 3 and all(re.fullmatch(r":?-+:?", cell) for cell in table[1]),
            "Keep the table header separator")
    require(all(len(row) == len(headers) for row in table), "Table rows must have the expected number of columns")
    return table[2:]


def account_table(text):
    headers = ["Account ID", "Entry count", "Net sales in cents"]
    result = []
    for row in markdown_table(text, headers):
        example = {
            "account_id": row[0],
            "transaction_count": integer(row[1], f"{row[0]} entry count"),
            "net_sales_cents": integer(row[2], f"{row[0]} net sales"),
        }
        result.append(example)
    return result


def totals_table(text, amount_column="Expected amount in cents"):
    names = {
        "Known customers": "known_net_cents",
        "Unmatched customers": "exceptions_net_cents",
        "All September entries": "source_net_cents",
    }
    result = {}
    for name, value in markdown_table(text, ["Check", amount_column]):
        require(name in names and names[name] not in result, "Keep one row for each of the three totals")
        result[names[name]] = integer(value, name)
    require(len(result) == 3, "Fill in all three totals")
    return result


def review_field(text, name):
    matches = re.findall(rf"^{re.escape(name)}: *(.+)$", text, re.MULTILINE)
    require(len(matches) == 1, f"Keep one {name}: line in your review")
    return matches[0].strip()


def check_evidence(root):
    text = safe_file(root, "verification/review-evidence.md").read_text(encoding="utf-8")
    for label in REVIEW_CHECKS:
        matches = re.findall(rf"^- \[([ xX])\] {re.escape(label)}[ \t]*$", text, re.MULTILINE)
        require(len(matches) == 1, f"Keep exactly one checklist item: {label}")
        require(matches[0].lower() == "x", f"Complete this review check before approval: {label}")
    require(review_field(text, "Decision") == "approved", "Analyst decision is not approved")


def verify(root, source_root=None, evidence=False):
    expected = expectations(source_root if source_root is not None else root)
    actual_report = read_csv(root, "reports/customer-account-report.csv", REPORT_FIELDS)
    actual_exceptions = read_csv(root, "reports/exceptions.csv", EXCEPTION_FIELDS)
    require(actual_report == expected["report"],
            "The customer report does not match the original data; check each customer's amounts, entry count, name, region, and row order")
    require(actual_exceptions == expected["exceptions"],
            "The unmatched-entry report does not match the original data; include each unique September entry whose customer is missing, with its original amount")
    if evidence:
        check_evidence(root)
    return expected["reconciliation"]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--source-root", type=Path)
    parser.add_argument("--evidence", action="store_true")
    args = parser.parse_args()
    try:
        totals = verify(args.root, args.source_root, args.evidence)
    except (VerificationError, OSError, csv.Error, UnicodeError, json.JSONDecodeError) as error:
        print(f"Verification failed: {error}", file=sys.stderr)
        return 1
    print("Independent verification passed: " + json.dumps(totals, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
