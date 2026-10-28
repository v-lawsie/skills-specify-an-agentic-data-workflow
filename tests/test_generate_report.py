import csv
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "src/generate_report.py"
FIXTURES = ROOT / "verification/fixtures"


class GenerateReportTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.data = self.root / "data"
        self.reports = self.root / "reports"
        self.data.mkdir()
        self.accounts = self.data / "customer-accounts.csv"
        self.transactions = self.data / "sales-transactions.csv"
        self.accounts.write_text(
            "account_id,account_type,region\n"
            "A200,Distributor,West\n"
            "A100,Retail,North\n"
            "A300,Retail,East\n",
            encoding="utf-8",
        )
        self.transactions.write_text(
            "transaction_id,account_id,transaction_date,amount_cents\n"
            "T1,A100,2026-09-01,1000\n"
            "T2,A100,2026-09-30,-200\n"
            "T2,A100,2026-09-30,-200\n"
            "T3,A200,2026-08-31,500\n"
            "T4,X900,2026-09-15,350\n"
            "T5,A200,2026-10-01,800\n",
            encoding="utf-8",
        )

    def tearDown(self):
        self.temporary.cleanup()

    def run_generator(self, accounts=None, transactions=None):
        command = [
            sys.executable, str(SCRIPT),
            "--accounts", str(accounts or self.accounts),
            "--transactions", str(transactions or self.transactions),
            "--output-dir", str(self.reports),
        ]
        return subprocess.run(command, capture_output=True, text=True, check=False)

    def read_report(self, name):
        with (self.reports / name).open(newline="", encoding="utf-8") as handle:
            return list(csv.DictReader(handle))

    def test_generates_sorted_totals_exceptions_and_zero_activity_accounts(self):
        result = self.run_generator()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(
            self.read_report("customer-account-report.csv"),
            [
                {
                    "account_id": "A100", "account_type": "Retail", "region": "North",
                    "transaction_count": "2", "net_sales_cents": "800",
                },
                {
                    "account_id": "A200", "account_type": "Distributor", "region": "West",
                    "transaction_count": "0", "net_sales_cents": "0",
                },
                {
                    "account_id": "A300", "account_type": "Retail", "region": "East",
                    "transaction_count": "0", "net_sales_cents": "0",
                },
            ],
        )
        self.assertEqual(
            self.read_report("exceptions.csv"),
            [{
                "transaction_id": "T4", "account_id": "X900",
                "transaction_date": "2026-09-15", "amount_cents": "350",
                "reason": "unknown_account",
            }],
        )

    def test_repeated_generation_is_byte_identical(self):
        first = self.run_generator()
        self.assertEqual(first.returncode, 0, first.stderr)
        before = {
            path.name: path.read_bytes()
            for path in self.reports.iterdir()
        }
        second = self.run_generator()
        self.assertEqual(second.returncode, 0, second.stderr)
        self.assertEqual(
            {path.name: path.read_bytes() for path in self.reports.iterdir()},
            before,
        )

    def test_supplied_invalid_fixtures_fail_without_reports(self):
        cases = [
            ("invalid-amount.csv", self.transactions),
            ("conflicting-transactions.csv", self.transactions),
            ("duplicate-accounts.csv", self.accounts),
        ]
        for fixture, target in cases:
            with self.subTest(fixture=fixture):
                with tempfile.TemporaryDirectory() as temporary:
                    root = Path(temporary)
                    data = root / "data"
                    data.mkdir()
                    accounts = data / "customer-accounts.csv"
                    transactions = data / "sales-transactions.csv"
                    shutil.copyfile(ROOT / "data/customer-accounts.csv", accounts)
                    shutil.copyfile(ROOT / "data/sales-transactions.csv", transactions)
                    (transactions if target == self.transactions else accounts).write_bytes(
                        (FIXTURES / fixture).read_bytes()
                    )
                    original_accounts = accounts.read_bytes()
                    original_transactions = transactions.read_bytes()
                    reports = root / "reports"
                    result = subprocess.run(
                        [
                            sys.executable, str(SCRIPT),
                            "--accounts", str(accounts),
                            "--transactions", str(transactions),
                            "--output-dir", str(reports),
                        ],
                        capture_output=True,
                        text=True,
                        check=False,
                    )
                    self.assertNotEqual(result.returncode, 0)
                    self.assertTrue(result.stderr.strip())
                    self.assertFalse((reports / "customer-account-report.csv").exists())
                    self.assertFalse((reports / "exceptions.csv").exists())
                    self.assertEqual(accounts.read_bytes(), original_accounts)
                    self.assertEqual(transactions.read_bytes(), original_transactions)

    def test_malformed_out_of_period_rows_still_fail(self):
        self.transactions.write_text(
            "transaction_id,account_id,transaction_date,amount_cents\n"
            "T1,A100,2026-08-31,01\n",
            encoding="utf-8",
        )
        result = self.run_generator()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("invalid amount", result.stderr)
        self.assertFalse(self.reports.exists())


if __name__ == "__main__":
    unittest.main()
