# Optional implementation reference

Learners do not need to read this page. The business brief and lesson comments
contain the instructions needed to complete the exercise.

<details>
<summary>Technical details for Copilot and exercise maintainers</summary>

## Output schemas

`reports/customer-account-report.csv`:

```csv
account_id,account_type,region,transaction_count,net_sales_cents
```

One row per known account, including inactive ones. Count unique in-period
transactions, including returns and zero-amount transactions. Copy account types
and regions exactly. Use integer counts and cents, never formatted currency.
Sort by account ID.

`reports/exceptions.csv`:

```csv
transaction_id,account_id,transaction_date,amount_cents,reason
```

One row per unique in-period transaction whose account ID is unknown, with reason
`unknown_account`. Include only the header if there are no exceptions. Sort by
transaction ID.

## Pull request totals summary

Include exactly one summary table in the pull request description, using these column names and row labels. Replace every TODO with a whole-number amount in cents, without dollar signs or commas.

```markdown
| Check | Amount in cents |
|---|---|
| Known customers | TODO |
| Unmatched customers | TODO |
| All September entries | TODO |
```

Calculate **Known customers** by summing `net_sales_cents` in the generated customer report and **Unmatched customers** by summing `amount_cents` in the generated exceptions report. Independently calculate **All September entries** from the original transaction export after deduplication and date filtering, keeping returns negative. The first two amounts must add up to the third. Do not copy the analyst's expected values instead of calculating the actual results. Update the description whenever the report changes. Do not add total rows to either CSV; their schemas stay unchanged.

Actions independently derive the correct totals from unchanged source data and verify the description's three values, as well as every report row. Missing, duplicate, malformed, or incorrect summary tables fail grading. Description edits rerun the pull request checks and Step 3 so a summary correction does not require an otherwise unnecessary code commit.

## Learner-readable evidence

The specification uses two Markdown tables under **Expected results**, not JSON.
The first has columns `Account ID`, `Entry count`, and `Net sales in cents`.
Require at least two distinct known accounts with correct source-derived values.
The second has columns `Check` and `Expected amount in cents`, and rows for
`Known customers`, `Unmatched customers`, and `All September entries`.

These tables record the expected comparisons; separate prose sections explaining the totals check and finished-report check are not required. Step 2 still grades the reporting rules and independently checks every expected customer value and each of the three totals.

The analyst completes `verification/review-evidence.md`, not the agent. It contains four review checklist items: compare the results for customers A100 and A200 with the specification's Expected results, check unmatched entries against the original customer list, confirm the totals reconcile and match the earlier calculations, and resolve any discrepancies. Require exactly one of each published checklist item marked `[x]` or `[X]`, plus one `Decision: approved` line. The analyst does not copy numbers or transaction IDs again or write a separate rationale. Do not infer human authorship or genuine review from these declarations.

## Verification commands

The coding agent runs these from the repository root and reports results in the PR:

```bash
python src/generate_report.py
python -m unittest discover -s tests
python verification/verify_report.py
```

For completed analyst evidence, run `python verification/verify_report.py --evidence`.
The verifier derives expectations directly from source data without importing the
implementation. It compares all account and exception rows, not just totals.
Source validation includes the negative fixtures under `verification/fixtures/`;
the agent should test its implementation against those fixtures too.

## Workflow checks

**Generated artifacts** checks protected files, deliverable presence, and all report
values, plus the pull request description's totals. **Analyst evidence** also checks the completed review checklist and declared
approval. It intentionally fails before the learner completes step 4.
**Reproduce and test** uses disposable working directories with no existing reports.
It requires the freshly generated reports to match the committed files byte for
byte, verifies them independently, repeats generation, and checks that sources
remain unchanged. It discovers and runs implementation tests, rejecting an empty
suite. Separate fresh copies replace one input with each of the three supplied
negative fixtures; the program must fail with an explanation and no partial
reports. All candidate execution stays in the unprivileged job.

Lesson progression does not execute learner code. Final completion runs on the merge's push to `main`, not a Copilot PR event, so it does not introduce another PR workflow-approval prompt. It independently locates the PR whose merge commit matches the pushed commit and still requires a merged same-repository PR into `main`, approved analyst evidence, correct reports and description totals, and a successful reproduction check on that PR's exact head. Direct pushes without a matching merged PR cannot complete the exercise.
Specification prose is checked for an answer rather than a word count; correct
table values are checked numerically. Neither establishes that the prose is
semantically complete.

</details>
