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

**Reporting period**: September 1 through September 30, 2026

**Sales and returns**: Subtract returns from sales by keeping their negative amounts. Count a return as an entry, not as a mistake. Keep amounts in US cents.

**Customers**: Match sales and returns to customers by account ID. Include every customer in the customer report, even those with no September activity.

**Repeated entries**: If an entry appears twice with the same transaction ID and identical details, count it only once. If the same transaction ID appears with different details, stop and ask for clarification. Do not choose one version.

## Unmatched customers

**Unmatched entries**: Put entries with unknown customer account IDs in reports/exceptions.csv, keeping their original amounts and signs. Do not guess which customer they belong to or silently discard them.

## When to stop

**Problems with the files**: Stop if an amount or date is unreadable, a required value is missing, or a customer account ID appears more than once in the customer list.

------------------------------

## Expected results

Enter whole numbers in cents, without dollar signs or commas.

| Account ID | Entry count | Net sales in cents |
|------------|-------------|--------------------|
| A100       | 3        | 18000               |
| A200       | 2        | 4000               |



| Check                 | Expected amount in cents |
|-----------------------|--------------------------|
| Known customers       | 22800                     |
| Unmatched customers   | 2750                     |
| All September entries | 25550                     |
