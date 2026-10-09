# Month-End Close Pack

Simulated month-end close for a retail finance team: reconciliations, BAS/IAS, FBT, fixed assets, payroll checks, rolling forecast and Python bank rec automation.

All figures are simulated and not based on any company's results.

## What's in here

- `Month_End_Close_Pack_Sep2026.xlsx`: the September 2026 close. Start with the Control tab, which shows every check passing.
- `automation/`: a Python script that matches bank statement lines to the cash book.

## For non-technical readers

Bank reconciliations normally mean ticking off every bank line against the accounting records by hand. The script does that matching automatically and lists only the items that need attention:

- Items that need a journal (on the bank statement, not in the books)
- Timing items (in the books, not yet at the bank), flagged if they are old

You don't need to run anything. Open `automation/exceptions_report.csv` to see the output, and the Automation tab in the workbook to see how it ties to the bank reconciliation.

## To run it yourself (optional, needs Python 3)

Put the four files in `automation/` in one folder, open a terminal in that folder and run:

    python3 bank_rec_automation.py sample_bank_statement.csv sample_gl_cash_book.csv --bank-balance 6638170 --gl-balance 7190000 --period-end 2026-09-30

It prints RECONCILED when the adjusted bank and ledger balances agree and writes `exceptions_report.csv`.

## Limits

Sample data only. Matching is on exact amount and date, so one-to-many items need manual review.
