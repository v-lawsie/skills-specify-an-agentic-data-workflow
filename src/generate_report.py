import argparse
import csv
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
PERIOD_START = date(2026, 9, 1)
PERIOD_END = date(2026, 9, 30)


class ReportError(ValueError):
    pass


def read_csv(path, expected_fields):
    rows = []
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.reader(handle, strict=True)
        try:
            header = next(reader)
        except StopIteration as error:
            raise ReportError(f"{path}: missing CSV header") from error
        if header != expected_fields:
            raise ReportError(
                f"{path}: expected header {','.join(expected_fields)}"
            )
        for number, values in enumerate(reader, 2):
            if len(values) != len(expected_fields):
                raise ReportError(f"{path}:{number}: wrong field count")
            if any(not value or value != value.strip() for value in values):
                raise ReportError(
                    f"{path}:{number}: fields must be nonempty and unpadded"
                )
            rows.append(dict(zip(expected_fields, values)))
    return rows


def load_accounts(path):
    accounts = {}
    for row in read_csv(path, ACCOUNT_FIELDS):
        account_id = row["account_id"]
        if account_id in accounts:
            raise ReportError(f"Duplicate account_id: {account_id}")
        accounts[account_id] = row
    return accounts


def load_transactions(path):
    transactions = {}
    for row in read_csv(path, TRANSACTION_FIELDS):
        transaction_id = row["transaction_id"]
        amount = row["amount_cents"]
        if not INTEGER.fullmatch(amount):
            raise ReportError(
                f"Transaction {transaction_id}: invalid amount_cents {amount}"
            )
        raw_date = row["transaction_date"]
        try:
            parsed_date = date.fromisoformat(raw_date)
        except ValueError as error:
            raise ReportError(
                f"Transaction {transaction_id}: invalid date {raw_date}"
            ) from error
        if parsed_date.isoformat() != raw_date:
            raise ReportError(
                f"Transaction {transaction_id}: date must use YYYY-MM-DD"
            )
        previous = transactions.get(transaction_id)
        if previous is not None and previous != row:
            raise ReportError(f"Conflicting transaction_id: {transaction_id}")
        transactions[transaction_id] = row
    return transactions


def build_reports(accounts_path, transactions_path):
    accounts = load_accounts(accounts_path)
    transactions = load_transactions(transactions_path)
    totals = {
        account_id: {"transaction_count": 0, "net_sales_cents": 0}
        for account_id in accounts
    }
    exceptions = []

    for transaction_id, row in sorted(transactions.items()):
        transaction_date = date.fromisoformat(row["transaction_date"])
        if not PERIOD_START <= transaction_date <= PERIOD_END:
            continue
        account_id = row["account_id"]
        amount = int(row["amount_cents"])
        if account_id not in accounts:
            exceptions.append({**row, "reason": "unknown_account"})
            continue
        totals[account_id]["transaction_count"] += 1
        totals[account_id]["net_sales_cents"] += amount

    report = []
    for account_id in sorted(accounts):
        report.append({
            **accounts[account_id],
            "transaction_count": str(totals[account_id]["transaction_count"]),
            "net_sales_cents": str(totals[account_id]["net_sales_cents"]),
        })
    return report, exceptions


def write_csv(path, fields, rows):
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def main(argv=None):
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description="Generate Lucerne's September customer reports.")
    parser.add_argument("--accounts", type=Path, default=root / "data/customer-accounts.csv")
    parser.add_argument("--transactions", type=Path, default=root / "data/sales-transactions.csv")
    parser.add_argument("--output-dir", type=Path, default=root / "reports")
    args = parser.parse_args(argv)

    try:
        report, exceptions = build_reports(args.accounts, args.transactions)
        args.output_dir.mkdir(parents=True, exist_ok=True)
        write_csv(args.output_dir / "customer-account-report.csv", REPORT_FIELDS, report)
        write_csv(args.output_dir / "exceptions.csv", EXCEPTION_FIELDS, exceptions)
    except (ReportError, OSError, csv.Error, UnicodeError) as error:
        print(f"Report generation failed: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
