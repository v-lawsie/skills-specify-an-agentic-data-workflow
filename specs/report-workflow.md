# Lucerne Publishing reporting instructions

## Purpose

A September net sales customer report to understand how much business each customer generated after returns.

## Audience

For the finance department of a publishing company to discuss the month's trading with account managers, and decide which accounts or unusual entries need follow-up.

## Inputs

The data/customer-accounts.csv file contains customer accounts: their account IDs, account types (Retail, Distributor, or Wholesale), and regions.
The data/sales-transactions.csv contains sales and returns: each entry's transaction ID, customer account ID, date, and amount.

## Outputs

The customer account report will be reports/customer-account-report.csv and should contain every customer, their number of September sales and returns, and their net sales. Include customers with no September activity, with both count and net sales set to zero.
The exceptions report will be reports/exceptions.csv and should contain sales and returns where there is no customer record in the customer list, so Finance can investigate before attributing them. Keep each entry's original amount and sign; do not guess its customer or silently omit it.

## Scope

The report should cover September only. Amounts are in US cents: 12500 means $125.00, and -2000 means a $20.00 return. Work in cents to keep amounts exact.

## Human approval

The business analyst must check and approve the report before the pull request is merged.

------------------------------

## How to prepare the report

**Reporting period**: TODO: Explain which dates belong in this report.

**Sales and returns**: TODO: Explain amounts in cents and how to handle returns.

**Customers**: TODO: Explain how to match customers and include those with no activity.

**Repeated entries**: TODO: Explain when an entry is counted once and when to stop.

## Unmatched customers

**Unmatched entries**: TODO: Explain what to do when a customer cannot be found.

## When to stop

**Problems with the files**: TODO: Explain which problems must stop the work rather than be guessed at.

------------------------------

## Expected results

Enter whole numbers in cents, without dollar signs or commas.

| Account ID | Entry count | Net sales in cents |
|------------|-------------|--------------------|
| A100       | TODO        | TODO               |
| A200       | TODO        | TODO               |



| Check                 | Expected amount in cents |
|-----------------------|--------------------------|
| Known customers       | TODO                     |
| Unmatched customers   | TODO                     |
| All September entries | TODO                     |
