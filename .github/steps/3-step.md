## Step 3: Ask Copilot to prepare the report

Your reporting instructions now describe both the result and the rules. Give them to Copilot and review what it produces.

### 📖 Theory: Give Copilot a clear task

GitHub Copilot can read your specification, write a program, and propose its changes in a pull request. Your specification tells it what the program must do. Keep the original data and your agreed instructions unchanged while Copilot works, so you can compare its report with the examples you already calculated.

### ⌨️ Activity 1: Give Copilot the task

1. Open the repository's **Issues** tab and create a new issue titled `Prepare Lucerne's September customer report`. Leave the exercise lesson issue alone.
1. Copy the task below into the new issue. You describe the outcome and review boundaries; Copilot reads the repository's technical instructions automatically.

   ```text
   Build a reusable workflow that produces the reports described in specs/report-workflow.md.
   Follow my rules and check the results against my examples.
   Include a summary of the totals for known customers, unmatched customers, and all September entries in the pull request description so I can compare them with my calculations.
   Keep the original data and specification unchanged.
   Ask me in this issue if anything is unclear.
   Open a pull request explaining your work and checks, and leave approval to me.
   ```

1. In the issue's **Assignees** field, choose **Copilot**. It will start work and link a pull request. Wait until it says the work is ready, then open that pull request.

   ![Select Copilot in the issue’s Assignees field](https://github.com/v-lawsie/skills-specify-an-agentic-data-workflow/blob/main/.github/images/create-issue.png?raw=true)

<details>
<summary>Having trouble? 🤷</summary><br/>

- If Copilot is not listed, check that your account and repository have access to Copilot in the cloud.
- Copilot may take several minutes or ask a question in the issue. Read and answer it before continuing.
- For help assigning the issue, see [GitHub's instructions](https://docs.github.com/en/copilot/how-tos/use-copilot-agents/coding-agent/create-a-pr).

</details>

### ⌨️ Activity 2: Check that the report was generated

1. Read Copilot's pull request description. Find its explanation of the report, the checks it ran, and a summary table with totals for **Known customers**, **Unmatched customers**, and **All September entries** in cents.
1. Open **Files changed**. Find both generated reports in `reports/`. Then confirm that neither original file in `data/`, nor your specification in `specs/report-workflow.md`, has been changed.
1. Go back to the Conversation tab and scroll down to the pull request's checks. GitHub may ask you to approve running the checks - if so, allow them to run.
1. Wait for **Generated artifacts** and **Reproduce and test** to pass. **Analyst evidence** will not pass yet: that check is waiting for your review in step 4.
1. If **Generated artifacts** or **Reproduce and test** fails, comment on the pull request with `@copilot`, describe the problem shown, and ask it to correct the work in this same pull request. Leave **Analyst evidence** for your own review in step 4. Leave the pull request open and unmerged. Mona checks the report when the pull request opens, its description is edited, or a corrective commit is added.
1. Wait a moment for Mona to check your work, provide feedback, and share the next lesson.

<details>
<summary>Having trouble? 🤷</summary><br/>

- A failed **Generated artifacts** or **Reproduce and test** check is feedback, not a reason to start over. Open it to see the explanation, then ask Copilot to correct the work.
- If no checks ran, look in the **Actions** tab for an approval request.
- If the pull request was created before this lesson appeared, close and reopen it without merging.
- Do not merge yet. You still need to check the figures yourself.

</details>
