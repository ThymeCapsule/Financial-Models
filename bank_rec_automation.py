#!/usr/bin/env python3
"""Bank reconciliation matching and exception report.

Matches bank statement lines to GL cash book lines, classifies what is left over
and proves the reconciliation:

    adjusted GL   = GL balance   + unmatched bank lines   (need a journal)
    adjusted bank = bank balance + unmatched GL lines     (timing items)
    the two adjusted balances must agree.

Matching rules
  1. Same amount (to the cent) and dates within +/- WINDOW days, one-to-one.
  2. Where several candidates qualify, the closest date wins (ties: earliest line).
  3. Unmatched bank line  -> "GL adjustment" (journal required).
  4. Unmatched GL line    -> "Timing"; "Timing - AGED" if open longer than AGED_DAYS.

Usage (sample data supplied alongside this script):
    python bank_rec_automation.py sample_bank_statement.csv sample_gl_cash_book.csv \
        --bank-balance 6638170 --gl-balance 7190000 --period-end 2026-09-30

Input CSVs need the columns: ref, date (YYYY-MM-DD), description, amount.
Standard library only. All sample data is simulated.
"""
import argparse
import csv
import datetime as dt
import sys
import time
from decimal import Decimal


def load(path):
    rows = []
    with open(path, newline="", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            rows.append({
                "ref": r["ref"].strip(),
                "date": dt.date.fromisoformat(r["date"].strip()),
                "description": r["description"].strip(),
                "amount": Decimal(r["amount"].strip()),
            })
    return rows


def match(bank, gl, window):
    """Greedy one-to-one match on exact amount and date window. Returns (pairs, bank_left, gl_left)."""
    by_amount = {}
    for b in bank:
        by_amount.setdefault(b["amount"], []).append(b)
    used = set()
    pairs = []
    for g in sorted(gl, key=lambda x: (x["date"], x["ref"])):
        cands = [b for b in by_amount.get(g["amount"], [])
                 if b["ref"] not in used and abs((b["date"] - g["date"]).days) <= window]
        if cands:
            best = min(cands, key=lambda b: (abs((b["date"] - g["date"]).days), b["date"], b["ref"]))
            used.add(best["ref"])
            pairs.append((g, best))
    matched_gl = {g["ref"] for g, _ in pairs}
    bank_left = [b for b in bank if b["ref"] not in used]
    gl_left = [g for g in gl if g["ref"] not in matched_gl]
    return pairs, bank_left, gl_left


def fmt(x):
    return f"{x:,.2f}"


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("bank_csv")
    ap.add_argument("gl_csv")
    ap.add_argument("--bank-balance", type=Decimal, required=True, help="closing balance per bank statement")
    ap.add_argument("--gl-balance", type=Decimal, required=True, help="closing balance per GL cash account")
    ap.add_argument("--period-end", type=dt.date.fromisoformat, required=True)
    ap.add_argument("--window", type=int, default=3, help="date tolerance in days (default 3)")
    ap.add_argument("--aged-days", type=int, default=30, help="ageing threshold in days (default 30)")
    ap.add_argument("--out", default="exceptions_report.csv")
    a = ap.parse_args(argv)

    t0 = time.perf_counter()
    bank, gl = load(a.bank_csv), load(a.gl_csv)
    pairs, bank_left, gl_left = match(bank, gl, a.window)

    exceptions = []
    for b in sorted(bank_left, key=lambda x: x["date"]):
        exceptions.append(["Bank statement", b["ref"], b["date"].isoformat(), b["description"], b["amount"],
                           "GL adjustment", "", "", "Journal required - Treasury"])
    for g in sorted(gl_left, key=lambda x: x["date"]):
        days = (a.period_end - g["date"]).days
        aged = days > a.aged_days
        exceptions.append(["GL cash book", g["ref"], g["date"].isoformat(), g["description"], g["amount"],
                           "Timing - AGED" if aged else "Timing", days, "Aged" if aged else "",
                           "Chase / reverse if stale" if aged else "Clears next period"])

    with open(a.out, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["source", "ref", "date", "description", "amount", "classification",
                    "days_open", "aged", "suggested_action"])
        w.writerows(exceptions)
    runtime = time.perf_counter() - t0

    adj_total = sum((b["amount"] for b in bank_left), Decimal(0))
    timing_total = sum((g["amount"] for g in gl_left), Decimal(0))
    adj_gl = a.gl_balance + adj_total
    adj_bank = a.bank_balance + timing_total
    diff = adj_gl - adj_bank
    aged_n = sum(1 for e in exceptions if e[7] == "Aged")

    print(f"Bank lines {len(bank)} | GL lines {len(gl)} | matched pairs {len(pairs)}")
    print(f"Unmatched bank lines (GL adjustments): {len(bank_left)}  total {fmt(adj_total)}")
    print(f"Unmatched GL lines (timing items):     {len(gl_left)}  total {fmt(timing_total)}  aged {aged_n}")
    print(f"Adjusted GL   {fmt(adj_gl)}   (GL {fmt(a.gl_balance)} + adjustments {fmt(adj_total)})")
    print(f"Adjusted bank {fmt(adj_bank)}   (bank {fmt(a.bank_balance)} + timing {fmt(timing_total)})")
    print(f"Difference    {fmt(diff)}   -> {'RECONCILED' if diff == 0 else 'INVESTIGATE'}")
    print(f"Exception report written to {a.out} | runtime {runtime:.3f}s")
    return 0 if diff == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
