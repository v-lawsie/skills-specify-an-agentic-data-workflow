# Optional data dictionary

Learners can follow the business brief without reading this reference.

<details>
<summary>Technical details for Copilot and exercise maintainers</summary>

All files are UTF-8 CSVs with one header row. Treat identifiers as case-sensitive
strings. Fields must be nonempty and have no leading/trailing whitespace. Headers
must match the documented order exactly; extra or missing fields are errors.

## Accounts

`data/customer-accounts.csv`: `account_id,account_type,region`

Each account ID is unique. Duplicate account IDs are errors, even if the rows
are identical. Account types (Retail, Distributor, or Wholesale in the supplied
data) and regions are descriptive text, not join keys.

## Transactions

`data/sales-transactions.csv`: `transaction_id,account_id,transaction_date,amount_cents`

- `transaction_id` is the deduplication key.
- `account_id` joins to accounts; unknown IDs are allowed but must be reported.
- `transaction_date` is a real calendar date written exactly `YYYY-MM-DD`.
- `amount_cents` is a signed base-10 integer in USD cents, with no plus sign,
  grouping, decimal point, or leading zeros (except `0`). Negative zero is invalid.

## Business rules

The learner explains these rules using the plain-language sections of the
specification. The short identifiers below are implementation shorthand, not
required learner terminology.

| Label | Required policy |
|---|---|
| `period` | Include 2026-09-01 through 2026-09-30, both inclusive. Exclude all other dates. |
| `money` | Compute in integer USD cents; preserve negative amounts as returns. No floating-point money calculations. |
| `join` | Join on account_id. Include every known account, with zero count and zero net when inactive. |
| `duplicates` | Keep one copy of fully identical transaction rows; conflicting rows with the same transaction_id are fatal errors. |
| `exceptions` | Output each unique in-period unknown-account transaction with reason `unknown_account`. Exclude it from account totals. |
| `reconciliation` | Known-account net plus exception net equals deduplicated in-period source net. Negative values participate with their signs. |
| `failure` | Validate all rows, even out-of-period rows. Missing/malformed fields or duplicate account IDs stop processing with a nonzero exit and an explanatory error. |
| `verification` | Recompute expectations from unchanged sources, inspect two accounts and an exception, run tests, and require the analyst's approval before merge. |

Deduplicate and validate across the entire transaction export before filtering the
period. Identical means all four field strings match, not just the ID or amount.
Do not silently skip an invalid row, coerce malformed amounts, or assume an unknown
account's identity. Fatal errors must leave no newly generated partial reports;
validate before writing either output.

## Repeatable execution

`python src/generate_report.py` runs from the repository root, reads the two
source paths above, and writes the two report paths in the acceptance criteria.
Create `reports/` if absent. Repeated runs must produce byte-identical outputs.
Sort account rows by `account_id` and exception rows by `transaction_id`, ascending.
End each CSV row with a newline; either LF or CRLF is accepted.

The interface for alternate test inputs is an implementation choice. Document it
in the PR and use it to test the supplied negative fixtures. Keep the default
command and output paths unchanged.

</details>
