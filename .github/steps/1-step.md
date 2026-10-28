## Step 1: Frame the business outcome

Lucerne Publishing sells books to bookstores and distributors. The Finance team needs a report showing each customer's net sales for September: sales minus returns. The information is in two separate files. One lists the customers, the other lists their sales and returns.

You are the business analyst helping Finance compile this report. You will write instructions for GitHub Copilot coding agent to combine the files and produce it. Those instructions are called a **specification**: they describe what to build, which rules to follow, and how to check the result.

Later, Copilot will propose a program and a report in a pull request, where you can inspect its changes before accepting them. You will compare the report with the original data to decide whether it is correct. You do not need to write the program yourself.

### 📖 Theory: Why write a specification?

Writing a clear specification instructs Copilot to build a report that meets your requirements, rather than guess or make decisions for you. The specification makes the purpose, audience, inputs, outputs, and scope clear before implementation starts, and gives you a shared reference for reviewing the result. You write the specification in plain language, just as you would write instructions for a colleague.


### Business brief

The Finance department is preparing its September month-end review. It needs to understand how much business each customer generated after returns, discuss the month's trading with account managers, and decide which accounts or unusual entries need follow-up.

The finance lead asks:

> "Combine our account export and sales export into a September net sales customer report.  Include accounts with no activity so we can distinguish a quiet account from one that has been missed. Flag anything that does not match, and show me that the figures account for the whole month's activity."

Use these two source files:

- **Account export** - `data/customer-accounts.csv` lists customer accounts: their account IDs, account types (Retail, Distributor, or Wholesale), and regions.
- **Sales export** - `data/sales-transactions.csv` lists sales and returns: each entry's transaction ID, customer account ID, date, and amount.

Amounts are in US cents: `12500` means $125.00, and `-2000` means a $20.00 return. Work in cents to keep amounts exact.

Finance needs two outputs:

- `reports/customer-account-report.csv`: every customer, their number of September sales and returns, and their net sales. Include customers with no September activity, with both count and net sales set to zero.
- `reports/exceptions.csv`: sales and returns where there is no customer record in the customer list, so Finance can investigate before attributing them. Keep each entry's original amount and sign; do not guess its customer or silently omit it.



### ⌨️ Activity: Write the workflow brief

1. Read Finance's business brief above.
1. Open the **Code** tab in your copied repository, open `specs/report-workflow.md`, and select the pencil icon to edit it on `main`.
1. Replace the TODO text in each section with your own response:

   - **Purpose**: What should the report show?
   - **Audience**: Who is the report for, and what will they use it for?
   - **Inputs**: Explain the information each input file provides.
   - **Outputs**: Describe the outputs - a customer report and a separate list of entries with unmatched customers.
   - **Scope**: Which month and currency are included? What will this report not cover?

   > Leave the other sections unchanged, you will define the calculation rules and checks in the next step.

1.  Create a **commit**: a saved version of the file with a message explaining what changed.
   - Select **Commit changes…** in the editor.
   - Enter a descriptive commit message, such as `Define the reporting outcome`.
   - Choose **Commit directly to the `main` branch**, rather than creating a new branch or pull request. For this exercise, Mona checks your specification on `main`. 
   - Select **Commit changes** to save. This records your instructions; it does not build or approve the report.
1. Wait a moment for Mona to check your work, provide feedback, and share the next lesson.

<details>
<summary>Having trouble? 🤷</summary><br/>

- The check reads `main`, not a draft branch. Confirm the branch before committing.
- Keep the scaffold's headings. Write meaningful sentences, not just a filename or "done."
- Be sure to remove all 'TODO:' comments before you commit.
- Check the active exercise issue's feedback and the **Step 1** Actions log.
- Passing means your specification has the required sections, names the input and output files, and says who must approve the report. It does not mean your instructions are correct or complete.

</details>
