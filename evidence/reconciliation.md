# Reconciliation — integration run (ledger scenario)

Generated 2026-11-23 09:11:53Z by `python tests/run.py --evidence`.
Python 3.10.12 on Linux-6.8.0-149-generic-x86_64-with-glibc2.35.

As of **2026-10-01**. 5 accounts, 39 ledger entries.

Tolerance is **zero dong**. There is no parameter in `reconcile()` that
could make it anything else.

| Account | Purpose | Ledger balance | Entries |
|---|---|---:|---:|
| `escrow:BR-1` | borrower account at partner bank | 0 | 14 |
| `escrow:L1` | lender escrow at partner bank | 7.368.220 | 8 |
| `escrow:L2` | lender escrow at partner bank | 3.157.807 | 8 |
| `platform:fees` | the platform's own fee income | 0 | 0 |
| `world` | outside the platform (external) | -10.526.027 | 9 |

| Check | Result |
|---|---|
| Balance breaks | none |
| Entry-chain breaks | none |
| Double-entry total across all accounts | 0 |
| **Verdict** | **PASSED** |

The double-entry total is zero, which is the arithmetic statement that
no money was created or destroyed anywhere in this run — every dong that
entered an account left another one.

## What this run was

Two lenders fund one 10.000.000 VND loan at 18.00% over 6 months; the borrower
repays every instalment; each repayment is distributed pro rata. Scope is
the money layer and the ledger (tasks T03-T08). The application, listing
and loan state machines are not in it yet, so this is not the full
lifecycle run of task T23 and does not claim to be.
