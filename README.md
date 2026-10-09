## For non-technical readers

Bank reconciliations normally mean ticking off every bank line against the
accounting records by hand. This script does that matching automatically and
lists only the items that need attention:

- Items that need a journal (on the bank statement, not in the books)
- Timing items (in the books, not yet at the bank), flagged if they are old

You don't need to run anything. See automation/exceptions_report.csv for the
output, and the Automation tab in the workbook for how it ties to the
reconciliation.

Technical users can run it with Python 3; the command is in the script header.
