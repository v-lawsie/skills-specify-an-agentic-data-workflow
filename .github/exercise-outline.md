# Specify an Agentic Data Workflow

## Exercise identity

| Item | Proposal |
|---|---|
| Approved repository name | `specify-an-agentic-data-workflow` |
| Learner copy | `skills-specify-an-agentic-data-workflow` |
| Target owner | `skills` |
| Copyright holder | Confirm before building the license and README footer |

## Welcome block

- **Who this is for:** Business analysts who can edit Markdown and navigate GitHub issues and pull requests.
- **What you’ll learn:** Define data contracts, specify reconciliation rules, delegate bounded work, and verify an agent-generated report.
- **What you’ll build:** A workflow specification, a Python report generator, a customer-account report, and verification evidence.
- **Prerequisites:** A GitHub account with access to Copilot coding agent, permission to run Actions, and familiarity with branches and pull requests. No Python authoring is required.
- **Time:** Approximately 60–90 minutes, plus coding-agent processing time.

## Learning objectives

Learners will be able to:

1. Translate a business brief into explicit inputs, outputs, constraints, and review responsibilities.
2. Specify joins, duplicate handling, exceptions, and measurable acceptance criteria.
3. Give a coding agent a bounded implementation task linked to the specification.
4. Independently reconcile a report to source records and document a release decision.

## Scenario and proposed data contract

You are a business analyst at **Lucerne Publishing**. Finance needs a customer-account sales report assembled from two synthetic exports:

| Source | Fields |
|---|---|
| `data/customer-accounts.csv` | `account_id`, `account_type`, `region` |
| `data/sales-transactions.csv` | `transaction_id`, `account_id`, `transaction_date`, `amount_cents` |

The proposed business rules are:

- Report September 2026 activity in USD, using integer cents throughout calculations.
- Join transactions to customer accounts by `account_id`; include every known account, including accounts with no activity.
- Treat negative amounts as returns, not invalid sales.
- Count identical repeated transaction records once. Conflicting records with the same transaction ID stop processing with a clear error.
- Exclude transactions outside the reporting period.
- Put in-period transactions with unknown account IDs in an exceptions file; never silently discard them.
- Stop on malformed required fields or duplicate account IDs rather than guessing.
- Require `known-account net + unknown-account exceptions net = deduplicated in-period source net`.
- Keep the inputs unchanged and require human approval before merging.

The fixture data will contain zero-activity accounts, returns, identical duplicates, unknown accounts, and date-boundary records. Separate test fixtures will exercise malformed and conflicting inputs.

These are **proposed rules for your approval**, not assumed publishing-industry standards.

## Learner journey

### Step 1: Frame the business outcome

**📖 Theory: A specification is a contract, not a wish**

An agent needs an observable outcome and clear boundaries, not just “combine these files.” A useful specification names the business audience, authoritative inputs, required outputs, and who approves the result. Separating business decisions from implementation choices prevents the agent from inventing reporting policy.

**⌨️ Activity: Write the workflow brief**

1. Read the business brief embedded in the step instructions and preview both source CSVs. — *GitHub UI*
2. Complete the purpose, audience, inputs, outputs, scope, and human-approval sections in `specs/report-workflow.md`. — *GitHub UI*
3. Commit the specification to `main`. — *GitHub UI; triggers validation*

**Troubleshooting:** Use the provided specification scaffold; keep the exact source paths; avoid including customer data beyond the supplied synthetic records.

**Transition**

- **Actions Trigger:** `push` to `main`, scoped to `specs/report-workflow.md`.
- **Grading-Check:** Custom specification checker requires populated sections, both source paths, defined report outputs, and an explicit human approval boundary. It rejects unchanged scaffold placeholders; feedback distinguishes structural checks from semantic judgment.
- **Learner artifact:** A business-focused first draft of the specification.

### Step 2: Make correctness testable

**📖 Theory: Define correctness before asking for implementation**

A join can produce plausible-looking but incorrect results when IDs are missing or repeated. Data contracts must state how to handle returns, duplicates, date boundaries, and exceptions. Acceptance criteria should connect report values to independently calculable source values.

**⌨️ Activity: Specify transformation and acceptance rules**

1. Use the reporting rules and checking guidance embedded in the step instructions to complete the transformation, exception, reconciliation, failure, and verification sections. The data dictionary and acceptance criteria remain optional technical references. — *GitHub UI*
2. Add at least two source-derived account examples, the overall reconciliation expectation, and a negative-input example with its expected failure. — *GitHub UI*
3. Commit the completed specification to `main`. — *GitHub UI; triggers validation*

**Troubleshooting:** Calculate in cents; distinguish identical duplicates from conflicting IDs; include unknown-account amounts in reconciliation, not in known-account totals.

**Transition**

- **Actions Trigger:** `push` to `main`, scoped to `specs/report-workflow.md`.
- **Grading-Check:** Custom checker requires the agreed rule coverage and checks structured acceptance examples against results derived from the supplied inputs. It does not claim that keyword coverage proves a good specification.
- **Learner artifact:** An implementation-ready specification with measurable acceptance criteria.

### Step 3: Delegate the report implementation

**📖 Theory: Bound the agent’s authority**

A coding agent can implement a specification, but it should not decide business policy or approve its own work. A bounded task identifies the controlling specification, permitted outputs, execution command, and stopping conditions. A pull request provides a place to inspect the implementation and its evidence before release.

**⌨️ Activity 1: Assign the implementation**

1. Create a GitHub issue using this exact task text. — *GitHub UI*

   ```text
   Implement the reporting workflow defined in specs/report-workflow.md.
   Treat that specification and the supplied data dictionary as authoritative.
   Create src/generate_report.py using only the Python standard library.
   Running python src/generate_report.py must produce
   reports/customer-account-report.csv and reports/exceptions.csv.
   Add tests/test_generate_report.py covering the specified rules and failures.
   Do not modify the source CSVs, specification, exercise workflows, or graders.
   If a business rule is missing or contradictory, stop and ask in the issue.
   Open a pull request with execution instructions and evidence.
   Do not merge it or claim that your own checks constitute human approval.
   ```

2. Assign the issue to Copilot coding agent and open its resulting pull request. — *GitHub UI*

**Troubleshooting — Activity 1:** Confirm coding-agent access first. If unavailable, the exercise is blocked at this step rather than silently switching tools.

**⌨️ Activity 2: Inspect the generated deliverables**

1. Read the PR diff and confirm the source files and specification are unchanged. — *GitHub UI*
2. Review the agent’s execution evidence and approve workflow execution if GitHub requires it. Request corrections through PR feedback when checks fail. — *GitHub UI*
3. Keep the PR unmerged until its generated-artifact check passes. Opening the PR or a corrective agent commit triggers validation. — *GitHub UI*

**Troubleshooting — Activity 2:** Check whether a workflow needs approval before diagnosing a grading failure. Do not merge to bypass a failed check.

**Transition**

- **Actions Trigger:** Same-repository `pull_request` events: opened, synchronize, reopened.
- **Grading-Check:** Custom checker validates output schemas and every account/exception value against independently derived expectations. It checks allowed changes and required artifacts; learner code is not executed in the privileged progression job.
- **Learner artifact:** An unmerged PR containing the generator, tests, and generated CSVs.

### Step 4: Independently verify and approve

**📖 Theory: Separate implementation evidence from verification**

An implementation can repeat the same mistake in its own tests. Independent verification recomputes expectations from source records and compares them with the submitted report. The analyst should inspect account-level examples, exception handling, and overall reconciliation before recording an approval decision.

**⌨️ Activity 1: Run independent verification**

1. Comment on the PR using this exact review request. — *GitHub UI; coding-agent instruction*

   ```text
   Run the supplied independent verifier:
   python verification/verify_report.py
   Run the implementation tests:
   python -m unittest discover -s tests
   Report the commands and results in this pull request.
   Do not edit the verifier, its fixtures, the source CSVs, or the specification.
   If a check fails, correct the implementation and regenerate the reports.
   Leave the final approval decision to me.
   ```

2. Read the independent verifier output and compare two account examples and one unknown-account exception directly with source rows. — *GitHub UI*

**Troubleshooting — Activity 1:** A passing implementation test is not a substitute for reconciliation. Request a correction if the report and specification disagree.

**⌨️ Activity 2: Record the analyst’s decision**

1. Complete `verification/review-evidence.json` on the PR branch with source-derived account examples, reconciliation amounts, reviewed exceptions, and your decision. — *GitHub UI*
2. Wait for the PR’s independent evidence check to pass; then merge the PR. — *GitHub UI; merge triggers completion validation*

**Troubleshooting — Activity 2:** Follow the supplied JSON scaffold; distinguish “checks passed” from your business approval; do not merge while corrections remain unresolved.

**Transition**

- **Actions Trigger:** `pull_request` synchronize validates evidence; closed-and-merged advances the final step.
- **Grading-Check:** Recompute report and evidence expectations from the source data; require correct account examples, exception coverage, reconciliation, an explicit approval decision, and unchanged protected exercise files. Recheck the merged result before posting completion.
- **Learner artifact:** A merged, reproducible reporting workflow and analyst verification record.

## Review recap

**Accomplishments:** Wrote a testable specification, delegated a bounded task, reconciled two sources, handled anomalies explicitly, and recorded a human approval decision.

**Next learning:** Live-system connectors, recurring execution, access controls, and production monitoring are follow-up topics—not part of this exercise.

## File map

| Files | Purpose |
|---|---|
| `.github/exercise-outline.md` | Approved outline, saved verbatim as the first bootstrap action |
| `README.md`, `LICENSE` | Welcome, Copy Exercise badge, MIT license, attribution |
| `.github/steps/1-step.md` | Frame the business outcome |
| `.github/steps/2-step.md` | Make correctness testable |
| `.github/steps/3-step.md` | Delegate implementation |
| `.github/steps/4-step.md` | Verify and approve |
| `.github/steps/x-review.md` | Completion recap |
| `.github/workflows/0-start-exercise.yml` | Start the exercise and post instructions |
| `.github/workflows/1-step.yml` through `4-step.yml` | Matching progression workflows; final workflow named `Step 4 # Last step of the exercise` |
| `.github/workflows/check-report.yml` | Unprivileged PR artifact/evidence checks |
| `.github/scripts/check_spec.py`, `.github/scripts/check_submission.py` | Structural specification and independent submission grading |
| `docs/business-brief.md`, `docs/data-dictionary.md`, `docs/acceptance-criteria.md` | Business context and explicit rule reference |
| `data/customer-accounts.csv`, `data/sales-transactions.csv` | Synthetic source data |
| `specs/report-workflow.md` | Learner specification scaffold |
| `verification/verify_report.py`, `verification/review-evidence.json` | Independent verifier and human evidence scaffold |
| `verification/fixtures/invalid-amount.csv`, `conflicting-transactions.csv`, `duplicate-accounts.csv` | Negative-input fixtures, all under `verification/fixtures/` |
| `verification/test_verify_report.py` | Author-side verifier regression coverage |
| Learner-created `src/generate_report.py`, `tests/test_generate_report.py`, `reports/customer-account-report.csv`, `reports/exceptions.csv` | Implementation deliverables |

## Success criteria and boundaries

All four steps are graded. Specification grading checks structure and concrete examples; it does **not** certify prose quality. Report grading independently checks exact values and reconciliation, while the analyst retains approval responsibility.

The build must keep write-capable exercise progression separate from execution of learner code, avoid `pull_request_target` execution of submitted code, and clearly explain any GitHub-required workflow approval. A live learner-copy run will still be needed to verify end-to-end progression.

## User-directed build revisions

The approved outline above is preserved as the original contract. During build
round 3, the user directed: "rewrite the remaining lessons in this style AND also
don't have them read technical things like the acceptance criteria. you can still
include these but hide them".

The lessons now use plain business language and are self-contained with the
business brief. Exact schemas and implementation commands remain in collapsed,
optional references for the coding agent and maintainers. Expected examples and
the analyst review use readable Markdown tables instead of JSON; the review file
is now `verification/review-evidence.md`. Bad-input behavior is explained in prose
rather than requiring learners to choose technical fixture paths. Independent
numeric grading, negative-fixture coverage, and the human approval boundary remain.

The user subsequently approved simplifying the step-3 issue request to business outcomes and review boundaries. Technical implementation requirements now live in `.github/copilot-instructions.md`, automatically read by Copilot coding agent, with links to the existing technical references. Required implementation artifacts, automated checks, and the analyst's exclusive responsibility for review evidence and approval remain unchanged.

The user also approved replacing repeated numerical review evidence in step 4 with a checklist. `verification/review-evidence.md` now records four completed comparisons and an explicit approval decision; learners reuse the calculations already in their specification instead of copying numbers and transaction IDs again. The evidence grader requires every checklist item and approval, while independent source-to-report verification, reproduction checks, and the merged-PR requirement remain unchanged.

The user approved asking Copilot to calculate the three reconciliation totals and include them in the pull request description. Step 4 compares that generated summary with the analyst's existing Expected results, without requiring the analyst to sum report rows again. Actions verify all three description totals against source data, and description edits rerun the PR checks and Step 3. CSV schemas, independent report verification, and the human approval boundary remain unchanged.

After a live run stalled at GitHub's Copilot PR workflow-approval gate, the user approved avoiding that extra prompt for completion. Step 4 now starts from the merge's push to `main`, resolves the merged PR for that exact commit, and retains independent artifact, description-total, analyst-approval, and exact-head reproduction checks. Its grading token explicitly includes `pull-requests: read`; direct pushes cannot substitute for merging the implementation PR. Earlier PR workflow approval is not bypassed.
