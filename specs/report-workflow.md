# Lucerne Publishing reporting instructions

## Purpose

TODO: Explain what the report should show.

## Audience

TODO: Explain who the report is for, and what they will use it for.

## Inputs
TODO:
The data/customer-accounts.csv file contains...
The data/sales-transactions.csv contains...

## Outputs

TODO: 
The customer account report will be reports/customer-account-report.csv and should contain...
The exceptions report will be reports/exceptions.csv and should contain...

## Scope

TODO: Explain which month and currency the report should cover.

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
