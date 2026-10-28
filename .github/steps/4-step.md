## Step 4: Check the figures and decide whether to accept the report

Copilot has produced the report. Check it against the original information before you tell Finance it is ready.

### 📖 Theory: Check the result, not just the explanation

When you use AI within a workflow, you must always verify its output. A report can look reasonable and still put amounts against the wrong customer or count the same sale twice. 

### ⌨️ Activity 1: Compare the report with the source

1. Post this comment on the existing pull request and Copilot will run the supplied checks:

   ```text
   @copilot Please check the reports against the original data and my specification.
   Run the checks, fix any errors, and update this pull request.
   Update the summary in the pull request description with totals for known customers, unmatched customers, and all September entries.
   Keep the original data and specification unchanged.
   Explain what you checked, what you changed, and any unresolved issues.
   Leave the review decision and approval to me; do not merge.
   ```

1. Open the `customer-account-report.csv` in the pull request. Find the two customers from your **Expected results** table and compare their entry counts and net sales with your calculations.
1. Open the `exceptions.csv` report. Find each listed entry in the original transaction file and confirm that its customer is missing from the customer list.
1. In the pull request description, compare the **Known customers**, **Unmatched customers**, and **All September entries** totals with your specification's **Expected results**. Known customers plus unmatched customers must equal all September entries. You do not need to add the report rows again. If the summary is missing or anything disagrees, ask Copilot to correct it before continuing.

<details>
<summary>Having trouble? 🤷</summary><br/>

- Use cents throughout your comparison and keep returns negative.
- A correct overall total does not prove that each customer's amount is correct.
- If you find an error in your own instructions, resolve it explicitly before accepting the report. Do not let Copilot quietly change the instructions to fit its answer.

</details>

### ⌨️ Activity 2: Complete the review checklist

1. In the repository's **Code** tab, switch from `main` to the branch shown at the top of Copilot's pull request.
1. Open `verification/review-evidence.md` and select the pencil icon. For each comparison you completed in Activity 1, replace `[ ]` with `[x]` beside the matching checklist item. 
1. If a comparison reveals a problem, leave its box unchecked and ask Copilot to correct the report. Compare the updated report again before marking that item complete.
1. When all four checks are complete and you are satisfied with the report, change **Decision** from `pending` to `approved`. Complete the checklist and approval yourself, not through Copilot, then commit the file to the pull request's branch.
1. Return to the pull request and wait for **Generated artifacts**, **Reproduce and test**, and **Analyst evidence** to pass. Correct any remaining problems before continuing.
1. If the pull request is a draft, mark it ready. Merge it into `main` to accept the work. The merge starts Mona's final check on `main`; closing the pull request without merging does not complete the exercise.
1. Wait a moment for Mona to check your work, confirm completion, and share the exercise recap.

<details>
<summary>Having trouble? 🤷</summary><br/>

- Keep the checklist wording unchanged and put an `x` inside each completed item's brackets.
- The checklist records your review, not new calculations. Use the **Expected results** you already wrote in step 2.
- Mona requires all four checked boxes and `Decision: approved`. Automated checks still verify the report's figures independently; checked boxes do not prove that you inspected them.
- If your review was committed to `main` by mistake, put it on the pull request's branch before merging.
- If you merged too early, correct the work in another pull request and merge it after all checks pass. Then run **Step 4** manually on `main` in the Actions tab, entering the number of the pull request that produced current `main`.

</details>
