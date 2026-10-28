## Step 2: Explain the rules and work out two examples

You have described the report Finance needs. Now work out the figures you expect, then add those calculations and the reporting rules to your specification.

### 📖 Theory: Decide what a correct result looks like

Before you ask Copilot to build the report, calculate a few expected results yourself and write down the constraints it must work within. You will use these later to check Copilot's work and decide whether to approve the workflow. Do the calculations first and keep them in your notes; you will open the specification editor only after you have everything ready.

#### How you will check the report

Before asking Copilot to build the report, you will manually calculate two customer sales values and the whole month's totals from the original data. You can then compare your calculations to Copilot's results to be able to validate and approve the workflow.

The customer-report total plus the unmatched-entry total must equal the total of all unique September entries. Calculate that source total independently so the check can reveal missing entries.

### ⌨️ Activity 1: Calculate the figures you will use to verify the report

1. Open `data/customer-accounts.csv` and `data/sales-transactions.csv` from the **Code** tab in separate browser tabs. For this activity you can use paper, a calculator, or a spreadsheet - you do not need to write code.
1. Prepare a working list of September transactions from `sales-transactions.csv`:

   - Keep only dates from September 1 through September 30, 2026 inclusive.
   - Compare transaction IDs. If an ID appears more than once with identical details, keep just one copy. If the details differ, stop rather than choose a version.
   - Keep the `amount_cents` values exactly as written, including negative signs for returns. Do not convert them to dollars.

1. Calculate the net sales for customers **A100** and **A200**:

   - For each account, find its entries in your working list and note their transaction IDs.
   - **Entry count** is the number of entries, including returns.
   - **Net sales in cents** is the sum of those entries' `amount_cents` values, with returns still negative.

1. Calculate **three totals for the whole month**, not just your two chosen customers:

   - **Known customers**: add the amounts of every entry in your working list whose account ID appears in `customer-accounts.csv`. Include all listed customers, not only the two examples.
   - **Unmatched customers**: add the amounts of every entry in your working list whose account ID does not appear in `customer-accounts.csv`.
   - **All September entries**: independently add every amount in your working list, whether the customer is known or unmatched.

1. Check that **Known customers + Unmatched customers = All September entries**. Calculate the last total from the source entries, rather than copying the sum of the first two: this gives you a separate check that no entries were missed.
1. Keep the two customer counts and net sales, the three totals, and your working notes ready for Activity 2. 

<details>
<summary>Having trouble? 🤷</summary><br/>

- As a separate example, a customer with a sale of `6000` and a return of `-1000` has an entry count of `2` and net sales of `5000` cents.
- The repeated T002 entry should count once, not twice.
- Exclude T011 and T012 because their dates fall outside September.
- Classify customers by whether their account IDs appear in the customer file, not by whether their amounts are positive.
- A negative customer total is valid: it means returns exceeded sales.
- Keep your calculations in notes until Activity 2, when you will add them to the specification together with the rules.

</details>

#### Finance's reporting rules

- Include September 1 through September 30, 2026. Leave out August and October.
- Match sales and returns to customers by account ID.
- Include every customer in the customer report, even those with no September activity.
- Subtract returns from sales by keeping their negative amounts. Count a return as an entry, not as a mistake. Keep amounts in US cents.
- If an entry appears twice with the same transaction ID and identical details, count it only once.
- If the same transaction ID appears with different details, stop and ask for clarification. Do not choose one version.
- Put entries with unknown customer account IDs in `reports/exceptions.csv`, keeping their original amounts and signs. Do not guess which customer they belong to or silently discard them.
- Stop if an amount or date is unreadable, a required value is missing, or a customer account ID appears more than once in the customer list.
- If work stops, explain which records need clarification. Do not present partially calculated reports as finished results.
- Keep the original files unchanged.

### ⌨️ Activity 2: Add the rules and calculations to your specification

1. Read **Finance's reporting rules** above. Use these and your calculations from Activity 1 to plan the remaining answers before opening the editor.
1. Open `specs/report-workflow.md` from the repository's **Code** tab, select `main`, and select the pencil icon to edit it.
1. Complete **How to prepare the report**, **Unmatched customers**, and **When to stop** in your own words, using Finance's rules. Keep the headings and bold rule labels.
1. Replace the TODO values in both **Expected results** tables with your calculations from Activity 1. Enter whole numbers in cents, without dollar signs or commas.
1. Read your specification once more. Have you explained what happens if the same transaction ID has two different amounts? Would someone following your instructions know to stop rather than choose one?
1. Confirm there are no TODOs left, then select **Commit changes…** and commit directly to `main`. Save the rules and calculations together in this one commit. These figures are your predictions; you will compare Copilot's report against them later.
1. Wait a moment for Mona to check your work, provide feedback, and share the next lesson.

<details>
<summary>Having trouble? 🤷</summary><br/>

- Describe the rules, not how to write a program. For example, say which entries belong in September's report rather than which code to use.
- Keep the section titles, bold rule labels, and table column names so Mona can find your answers.
- Add the calculations you already made in Activity 1; you do not need to work them out again while editing.
- Mona can check your calculations and whether sections are filled in. You still need to read the instructions for clarity.

</details>
