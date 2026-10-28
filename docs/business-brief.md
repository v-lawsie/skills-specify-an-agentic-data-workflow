# Lucerne Publishing: customer-account reporting brief

Lucerne Publishing is a fictional company that sells books to bookstores and
distributors. Finance is preparing its September 2026 month-end review. The team
can see individual sales and returns, but it does not yet have a reliable view
of how much business each customer generated after returns. It needs that view
to discuss the month's trading with account managers and decide which accounts
or unusual entries need follow-up.

The information comes from two exports. One lists customer accounts, meaning the
businesses that buy books from Lucerne. The other lists sales and returns.
You are the business analyst asked to explain how these files should be combined
and how Finance can check the report.

The finance lead asks:

> "Combine our account export and sales export into a September customer report.
> I want Finance and the account managers working from the same figures, not
> separate spreadsheets. Include accounts with no activity so we can distinguish
> a quiet account from one that has been missed. Flag anything that does not
> match, and show me that the figures account for the whole month's activity."

You will write a **specification**: instructions describing the required report,
the calculation rules, and the checks that show whether the result is correct.
GitHub Copilot coding agent will then use those instructions to propose a program
and its report in a pull request. Your job is to compare the report with the
original data before deciding whether to accept the work.

## What Finance needs

The customer report should list every customer, the number of September sales
and returns recorded for them, and their net sales. Include customers with no
September activity: their count and net sales should both be zero.

Save this as `reports/customer-account-report.csv`. Finance will use it for the
month-end review, and account managers will use it to identify customers whose
sales, returns, or lack of activity deserve a closer look.

Some sales entries may refer to a customer missing from the customer list.
Save those entries separately in `reports/exceptions.csv` so Finance can
investigate the account details before attributing the sales or returns.
Keep each entry's original amount, including the sign. Do not guess which
customer it belongs to or leave it out without explanation.

## The two source files

- [data/customer-accounts.csv](../data/customer-accounts.csv) is the customer list. Each customer has an account
  ID, an account type (Retail, Distributor, or Wholesale), and a region.
- [data/sales-transactions.csv](../data/sales-transactions.csv) lists sales and returns. Each entry has a
  transaction ID, a customer account ID, a date, and an amount.

Use the account IDs to match the files, not the account types or regions.
Amounts are stored in US cents: `12500` means $125.00, and `-2000` means a
$20.00 return. Work in cents so the amounts remain exact.

All records are invented. The company name is scenario context, not a claim of
affiliation. Do not upload workplace data or connect live systems.

## Scope

Produce September 2026 net sales in USD by account, plus a separate exception
report. This is not an outstanding-balance report: there are no invoices, payment
dates, taxes, exchange rates, or opening balances in the inputs. Do not infer them.
Recurring automation and live connectors are out of scope.

## Finance's reporting rules

- Include September 1 through September 30, 2026. Leave out August and October.
- Subtract returns from sales. Count a return as an entry, not as a mistake.
- If an entry appears twice with the same transaction ID and identical details,
  count it only once.
- If the same transaction ID appears with different details, stop and ask for
  clarification. Do not choose one version.
- Stop if an amount or date is unreadable, a required value is missing, or a
  customer account ID appears more than once in the customer list.
- If work stops, explain which records need clarification. Do not present
  partially calculated reports as finished results.
- Keep the original files unchanged.

## How you will check the report

Before asking Copilot to build it, choose two customers and calculate what their
report rows should show. List each customer's September transaction IDs, count
each unique entry once, and add its sales and returns with their original signs.

Also add up the whole month's unique entries. The customer-report total plus the
unmatched-entry total should equal that source total. This checks that nothing
has been lost between the two files and the finished reports.

Record these predictions in the two **Expected results** tables in
`specs/report-workflow.md`: an entry count and net sales in cents for each of
your two chosen customers, then three amounts in cents covering the whole month
(all known customers, all unmatched customers, and all September entries).
Calculate the last amount directly from the source, independently of the first
two. Step 2 walks you through this as a separate activity. A calculator or
spreadsheet is fine; keep your working notes and transaction IDs for the review.

After Copilot produces the report, compare its rows with your calculations.
Check the unmatched entries too. As the business analyst, record the evidence
and your approval decision before the pull request is merged. Copilot producing
files is not approval: Finance should receive a report that you have checked
against the original exports, with any unresolved entries clearly identified.
