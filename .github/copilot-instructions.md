# Reporting implementation instructions

When implementing, checking, or correcting the reporting workflow for this exercise:

- Treat [the analyst's specification](../specs/report-workflow.md) as the business requirements. Follow its reporting rules and expected examples. If anything is missing, unclear, or contradictory, ask in the assigned issue rather than guessing or changing the specification.
- Read [the data dictionary](../docs/data-dictionary.md) and [the implementation reference](../docs/acceptance-criteria.md) for the required input formats, output schemas, execution contract, and verification commands.
- Create `src/generate_report.py` using only the Python standard library. Running `python src/generate_report.py` from the repository root must generate `reports/customer-account-report.csv` and `reports/exceptions.csv`.
- Add runnable `unittest` tests in `tests/test_generate_report.py` covering the reporting rules and the supplied invalid-input fixtures. Generation must work without existing reports, be repeatable, and leave the source files unchanged. Invalid inputs must stop with an explanation and no partial reports.
- Run the generation, implementation tests, and independent verification commands listed in the implementation reference. Commit the program, tests, and both generated reports.
- Include the three-total summary table specified in the implementation reference in the pull request description. Sum known-customer amounts from the generated customer report and unmatched amounts from the generated exceptions report. Independently total all unique September source entries, keeping returns negative. Do not copy the specification's expected values as a substitute for calculating the results. Keep this table current when reports are corrected.
- When asked to check or correct an existing pull request, rerun those commands. If a check fails, correct the implementation and regenerate the reports in that same pull request. Explain the checks run, changes made, and any unresolved failures; do not claim success while failures remain.
- Limit implementation changes to Python files under `src/` and `tests/` and the two generated report files. Do not change the original data, specification, repository instructions, documentation, workflows, or exercise checking files to make checks pass.
- Leave `verification/review-evidence.md` for the analyst to complete. The **Analyst evidence** check is expected to fail until that human review; do not write an approval decision on the analyst's behalf.
- Open a pull request explaining what was produced and which checks passed or failed. Leave it unmerged for the analyst to review and approve.
