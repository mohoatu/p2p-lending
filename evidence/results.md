# Test results

Generated 2026-11-23 09:11:53Z by `python tests/run.py --evidence`.
Python 3.10.12 on Linux-6.8.0-149-generic-x86_64-with-glibc2.35.

Every check carries the specification identifiers it proves, so this file
answers "what was proven?" rather than only "did it pass?".

| Suite | Checks | Passed | Failed |
|---|---:|---:|---:|
| unit: money | 47 | 47 | 0 |
| unit: schedule | 68 | 68 | 0 |
| unit: payment | 70 | 70 | 0 |
| unit: distribution | 22 | 22 | 0 |
| unit: ledger | 32 | 32 | 0 |
| negative: ledger | 35 | 35 | 0 |
| integration: ledger | 34 | 34 | 0 |
| **total** | **308** | **308** | **0** |

## unit: money

| Result | Ids | Check |
|---|---|---|
| pass | `R6` | an int passes through unchanged |
| pass | `R6` | zero is a valid amount |
| pass | `R6` | a negative amount is valid (ledger entries have direction) |
| pass | `R6` | a float is refused, not rounded |
| pass | `R6` | a float with a fraction is refused |
| pass | `R6` | a Decimal is refused |
| pass | `R6` | a numeric string is refused |
| pass | `R6` | None is refused |
| pass | `R6` | True is refused despite being an int subclass |
| pass | `R6` | False is refused for the same reason |
| pass | `R6` | exactly half rounds up |
| pass | `R6` | just under half rounds down |
| pass | `R6` | just over half rounds up |
| pass | `R6` | 1.5 rounds to 2 |
| pass | `R6` | 2.5 rounds to 3, not to 2 (not banker's rounding) |
| pass | `R6` | 3.5 rounds to 4 |
| pass | `R6` | an exact division is untouched |
| pass | `R6` | minus a half rounds away from zero |
| pass | `R6` | minus 2.5 rounds to minus 3 |
| pass | `R6` | minus just under half rounds toward zero |
| pass | `R6` | a zero denominator is refused |
| pass | `R6` | a negative denominator is refused |
| pass | `I6` | an even split is even |
| pass | `I6` | the residue lands on the last part |
| pass | `I6` | a residue of two also lands last |
| pass | `I6` | one part takes everything |
| pass | `I6` | allocate(100, 3) sums exactly to the total |
| pass | `I6` | allocate(100, 3) returns the requested number of parts |
| pass | `I6` | allocate(1000000, 7) sums exactly to the total |
| pass | `I6` | allocate(1000000, 7) returns the requested number of parts |
| pass | `I6` | allocate(12345679, 18) sums exactly to the total |
| pass | `I6` | allocate(12345679, 18) returns the requested number of parts |
| pass | `I6` | allocate(5000000, 24) sums exactly to the total |
| pass | `I6` | allocate(5000000, 24) returns the requested number of parts |
| pass | `I6` | zero parts is refused |
| pass | `I6` | a negative number of parts is refused |
| pass | `I6` | a full year at 12% on ten million is 1,200,000 |
| pass | `I6` | zero days accrues nothing |
| pass | `I6` | a zero rate accrues nothing |
| pass | `I6` | a zero balance accrues nothing |
| pass | `I6` | a negative rate is refused |
| pass | `I6` | a negative number of days is refused |
| pass | `I6` | a float balance is refused |
| pass | `A4.2` | thousands are grouped with a dot |
| pass | `A4.2` | a short amount is unchanged |
| pass | `A4.2` | zero formats as zero |
| pass | `A4.2` | a negative amount keeps its sign |

## unit: schedule

| Result | Ids | Check |
|---|---|---|
| pass | `A4.3` | one month on from 15 Jan is 15 Feb |
| pass | `A4.3` | 31 Jan plus one month clamps to 28 Feb, not 3 Mar |
| pass | `A4.3` | 31 Jan 2028 plus one month clamps to 29 Feb in a leap year |
| pass | `A4.3` | twelve months on crosses the year |
| pass | `A4.3` | two months from December lands in February |
| pass | `A1.3` | a 3-month term is accepted |
| pass | `A1.3` | a 6-month term is accepted |
| pass | `A1.3` | a 12-month term is accepted |
| pass | `A1.3` | a 18-month term is accepted |
| pass | `A1.3` | a 24-month term is accepted |
| pass | `A1.3` | a 7-month term is refused |
| pass | `A1.3` | a zero term is refused |
| pass | `A1.3` | a free-text term is refused |
| pass | `A4.1` | a float principal is refused |
| pass | `A4.1` | a zero principal is refused |
| pass | `A4.1` | a negative rate is refused |
| pass | `A4.1` | a string date is refused |
| pass | `I6 A4.4` | 5000000 VND / 1500 bps / 3m: principal columns sum to the principal |
| pass | `I6 A4.4` | 5000000 VND / 1500 bps / 3m: instalment totals sum to total repayable |
| pass | `I6 A4.4` | 5000000 VND / 1500 bps / 3m: total repayable is principal plus total interest |
| pass | `A4.3` | 5000000 VND / 1500 bps / 3m: every instalment has a non-negative interest figure |
| pass | `A4.3` | 5000000 VND / 1500 bps / 3m: due dates are strictly increasing |
| pass | `A4.3` | 5000000 VND / 1500 bps / 3m: sequence numbers run 1..n without a gap |
| pass | `I6 A4.4` | 7000000 VND / 1800 bps / 6m: principal columns sum to the principal |
| pass | `I6 A4.4` | 7000000 VND / 1800 bps / 6m: instalment totals sum to total repayable |
| pass | `I6 A4.4` | 7000000 VND / 1800 bps / 6m: total repayable is principal plus total interest |
| pass | `A4.3` | 7000000 VND / 1800 bps / 6m: every instalment has a non-negative interest figure |
| pass | `A4.3` | 7000000 VND / 1800 bps / 6m: due dates are strictly increasing |
| pass | `A4.3` | 7000000 VND / 1800 bps / 6m: sequence numbers run 1..n without a gap |
| pass | `I6 A4.4` | 10000000 VND / 1200 bps / 12m: principal columns sum to the principal |
| pass | `I6 A4.4` | 10000000 VND / 1200 bps / 12m: instalment totals sum to total repayable |
| pass | `I6 A4.4` | 10000000 VND / 1200 bps / 12m: total repayable is principal plus total interest |
| pass | `A4.3` | 10000000 VND / 1200 bps / 12m: every instalment has a non-negative interest figure |
| pass | `A4.3` | 10000000 VND / 1200 bps / 12m: due dates are strictly increasing |
| pass | `A4.3` | 10000000 VND / 1200 bps / 12m: sequence numbers run 1..n without a gap |
| pass | `I6 A4.4` | 12345679 VND / 2400 bps / 18m: principal columns sum to the principal |
| pass | `I6 A4.4` | 12345679 VND / 2400 bps / 18m: instalment totals sum to total repayable |
| pass | `I6 A4.4` | 12345679 VND / 2400 bps / 18m: total repayable is principal plus total interest |
| pass | `A4.3` | 12345679 VND / 2400 bps / 18m: every instalment has a non-negative interest figure |
| pass | `A4.3` | 12345679 VND / 2400 bps / 18m: due dates are strictly increasing |
| pass | `A4.3` | 12345679 VND / 2400 bps / 18m: sequence numbers run 1..n without a gap |
| pass | `I6 A4.4` | 99999997 VND / 2050 bps / 24m: principal columns sum to the principal |
| pass | `I6 A4.4` | 99999997 VND / 2050 bps / 24m: instalment totals sum to total repayable |
| pass | `I6 A4.4` | 99999997 VND / 2050 bps / 24m: total repayable is principal plus total interest |
| pass | `A4.3` | 99999997 VND / 2050 bps / 24m: every instalment has a non-negative interest figure |
| pass | `A4.3` | 99999997 VND / 2050 bps / 24m: due dates are strictly increasing |
| pass | `A4.3` | 99999997 VND / 2050 bps / 24m: sequence numbers run 1..n without a gap |
| pass | `I6 A4.4` | 100000000 VND / 1000 bps / 24m: principal columns sum to the principal |
| pass | `I6 A4.4` | 100000000 VND / 1000 bps / 24m: instalment totals sum to total repayable |
| pass | `I6 A4.4` | 100000000 VND / 1000 bps / 24m: total repayable is principal plus total interest |
| pass | `A4.3` | 100000000 VND / 1000 bps / 24m: every instalment has a non-negative interest figure |
| pass | `A4.3` | 100000000 VND / 1000 bps / 24m: due dates are strictly increasing |
| pass | `A4.3` | 100000000 VND / 1000 bps / 24m: sequence numbers run 1..n without a gap |
| pass | `I6 A4.4` | 5000001 VND / 3300 bps / 3m: principal columns sum to the principal |
| pass | `I6 A4.4` | 5000001 VND / 3300 bps / 3m: instalment totals sum to total repayable |
| pass | `I6 A4.4` | 5000001 VND / 3300 bps / 3m: total repayable is principal plus total interest |
| pass | `A4.3` | 5000001 VND / 3300 bps / 3m: every instalment has a non-negative interest figure |
| pass | `A4.3` | 5000001 VND / 3300 bps / 3m: due dates are strictly increasing |
| pass | `A4.3` | 5000001 VND / 3300 bps / 3m: sequence numbers run 1..n without a gap |
| pass | `A4.4` | a principal not divisible by the term leaves a residue |
| pass | `A4.4` | the final instalment carries the extra dong |
| pass | `A4.4` | nominal instalment times the term overstates the total |
| pass | `A4.2` | the final period's interest is far below the first's |
| pass | `A4.2` | interest rises exactly once, after the short February period |
| pass | `A4.2` | the rise is from the February period to the March one |
| pass | `A4.3` | the same inputs produce an identical schedule |
| pass | `I6` | an interest-free loan repays exactly the principal |
| pass | `I6` | an interest-free loan accrues no interest |

## unit: payment

| Result | Ids | Check |
|---|---|---|
| pass | `C1.1` | the application order is fees, late interest, interest, principal |
| pass | `C1.1` | a full payment produces one row per bucket |
| pass | `C1.1` | fees are satisfied first |
| pass | `C1.1` | late interest is satisfied second |
| pass | `C1.1` | interest is satisfied third |
| pass | `C1.1` | principal is satisfied last |
| pass | `I4` | a full payment sums to the amount received |
| pass | `C1.1` | a payment under the fee produces exactly one row |
| pass | `C1.1` | that row is the fee |
| pass | `I4` | it sums to the amount received |
| pass | `C1.1` | no principal is touched |
| pass | `C1.1` | no interest is touched |
| pass | `C1.1` | the fee is fully satisfied |
| pass | `C1.1` | late interest is fully satisfied |
| pass | `C1.1` | interest takes only what is left |
| pass | `C1.1` | principal is untouched |
| pass | `I4` | a partial payment sums to the amount received |
| pass | `C1.3` | principal absorbs up to the whole outstanding balance |
| pass | `C1.3` | what remains after the debt is recorded as unapplied |
| pass | `I4` | an overpayment still sums to the amount received |
| pass | `I4` | an overpayment loses nothing — no row is silently dropped |
| pass | `I4` | with nothing owed the whole payment is unapplied |
| pass | `I4` | and it still sums to the amount received |
| pass | `I4` | 1 dong: the rows sum to the amount received |
| pass | `I4` | 1 dong: every row is a positive amount |
| pass | `C1.1` | 1 dong: rows are numbered 1..n in order |
| pass | `I4` | 7 dong: the rows sum to the amount received |
| pass | `I4` | 7 dong: every row is a positive amount |
| pass | `C1.1` | 7 dong: rows are numbered 1..n in order |
| pass | `I4` | 49999 dong: the rows sum to the amount received |
| pass | `I4` | 49999 dong: every row is a positive amount |
| pass | `C1.1` | 49999 dong: rows are numbered 1..n in order |
| pass | `I4` | 50000 dong: the rows sum to the amount received |
| pass | `I4` | 50000 dong: every row is a positive amount |
| pass | `C1.1` | 50000 dong: rows are numbered 1..n in order |
| pass | `I4` | 50001 dong: the rows sum to the amount received |
| pass | `I4` | 50001 dong: every row is a positive amount |
| pass | `C1.1` | 50001 dong: rows are numbered 1..n in order |
| pass | `I4` | 279999 dong: the rows sum to the amount received |
| pass | `I4` | 279999 dong: every row is a positive amount |
| pass | `C1.1` | 279999 dong: rows are numbered 1..n in order |
| pass | `I4` | 280000 dong: the rows sum to the amount received |
| pass | `I4` | 280000 dong: every row is a positive amount |
| pass | `C1.1` | 280000 dong: rows are numbered 1..n in order |
| pass | `I4` | 280001 dong: the rows sum to the amount received |
| pass | `I4` | 280001 dong: every row is a positive amount |
| pass | `C1.1` | 280001 dong: rows are numbered 1..n in order |
| pass | `I4` | 1279999 dong: the rows sum to the amount received |
| pass | `I4` | 1279999 dong: every row is a positive amount |
| pass | `C1.1` | 1279999 dong: rows are numbered 1..n in order |
| pass | `I4` | 1280001 dong: the rows sum to the amount received |
| pass | `I4` | 1280001 dong: every row is a positive amount |
| pass | `C1.1` | 1280001 dong: rows are numbered 1..n in order |
| pass | `I4` | 9999999 dong: the rows sum to the amount received |
| pass | `I4` | 9999999 dong: every row is a positive amount |
| pass | `C1.1` | 9999999 dong: rows are numbered 1..n in order |
| pass | `I4` | a zero payment is refused |
| pass | `I4` | a negative payment is refused |
| pass | `I4` | a float payment is refused |
| pass | `I4` | an unknown bucket is refused |
| pass | `I4` | a negative amount owed is refused |
| pass | `I4` | a float amount owed is refused |
| pass | `C1.4` | a settlement quote is principal plus interest to date |
| pass | `C1.4` | the quote is strictly less than one with a day of future interest |
| pass | `C1.4` | fees and late interest are included when present |
| pass | `C1.4` | a settled loan quotes zero |
| pass | `C1.4` | a negative principal is refused |
| pass | `C1.4` | a float in a quote is refused |
| pass | `C1.4` | paying the quote leaves nothing unapplied |
| pass | `C1.4` | paying the quote clears the principal |

## unit: distribution

| Result | Ids | Check |
|---|---|---|
| pass | `I5 C2.2` | three equal lenders, 100 dong: the parts sum to 100 |
| pass | `C2.2` | the residue goes to the earliest commitment on a tie |
| pass | `C2.2` | the later lenders take the floor |
| pass | `I5` | three equal lenders, 101 dong: the parts sum to 101 |
| pass | `C2.2` | the two earliest each take a dong |
| pass | `C2.2` | the latest takes the floor |
| pass | `C2.1` | a 70% share receives 700,000 |
| pass | `C2.1` | a 20% share receives 200,000 |
| pass | `C2.1` | a 10% share receives 100,000 |
| pass | `I5` | an exact split sums to the amount |
| pass | `I5` | a sole lender receives the whole amount |
| pass | `C2.2` | allocations come back in the order the shares were given |
| pass | `C2.2` | the same inputs distribute identically |
| pass | `I5` | a simultaneous tie still sums exactly |
| pass | `C2.2` | the lower identifier takes the extra dong |
| pass | `I5 C2.3` | 2,000 random splits all sum exactly to the amount (seed 20261123) |
| pass | `I5` | a zero amount is refused |
| pass | `I5` | a negative amount is refused |
| pass | `I5` | a float amount is refused |
| pass | `I5` | an empty share list is refused |
| pass | `I5` | a zero commitment is refused — it would be a lender with no stake |
| pass | `I5` | a float commitment is refused |

## unit: ledger

| Result | Ids | Check |
|---|---|---|
| pass | `R6` | a new ledger has nothing in it |
| pass | `R6` | every opened account starts at zero |
| pass | `R6` | the double-entry total of an empty ledger is zero |
| pass | `R6` | a two-leg posting creates two entries |
| pass | `R6` | the receiving account holds the money |
| pass | `R6` | the external account is negative by the same amount |
| pass | `I2` | the total across all accounts is still zero |
| pass | `R6` | a three-leg transaction moves from two accounts to one |
| pass | `R6` | the first lender's escrow fell by its leg |
| pass | `R6` | the second lender's escrow fell by its leg |
| pass | `I2` | the total is still zero after a multi-leg transaction |
| pass | `I9` | the lender's account has two entries |
| pass | `I9` | the first entry has no predecessor |
| pass | `I9` | the second entry points at the first |
| pass | `I9` | sequence numbers run 1..n within the account |
| pass | `I9` | the chain is unbroken for escrow:BR-1 |
| pass | `I9` | the chain is unbroken for escrow:L1 |
| pass | `I9` | the chain is unbroken for escrow:L2 |
| pass | `I9` | the chain is unbroken for world |
| pass | `R6` | entries carry the references they were posted with |
| pass | `R6` | a transaction can be retrieved by its reference |
| pass | `R6` | a correction adds entries rather than removing any |
| pass | `R6` | the original posting is still in the ledger |
| pass | `R6` | the reversal restored the first lender |
| pass | `R6` | the reversal emptied the borrower account |
| pass | `I2` | the total is zero after the correction |
| pass | `R6` | entries() returns a tuple, not the internal list |
| pass | `R6` | entries_for() returns a tuple |
| pass | `R6` | a caller cannot grow the ledger through a returned value |
| pass | `R6` | two hundred postings accumulate correctly |
| pass | `I9` | the chain is unbroken across two hundred entries |
| pass | `I2` | the total is still zero across two hundred entries |

## negative: ledger

| Result | Ids | Check |
|---|---|---|
| pass | `R6` | the amount on a posted entry cannot be changed |
| pass | `R6` | the account on a posted entry cannot be changed |
| pass | `R6` | the chain link on a posted entry cannot be rewritten |
| pass | `R6` | the Ledger class has no update, delete, amend or override method |
| pass | `R6` | the only method that changes the ledger is post() |
| pass | `I2` | a transaction with more going in than out is refused |
| pass | `I2` | a transaction with more going out than in is refused |
| pass | `I2` | a one-dong imbalance is refused, the same as a large one |
| pass | `I2` | a single-leg posting is refused — money must come from somewhere |
| pass | `I2` | an empty posting is refused |
| pass | `R6` | a zero-amount leg is refused |
| pass | `R6` | a negative leg is refused — direction carries the sign, not the amount |
| pass | `R6` | a float amount is refused at the ledger boundary too |
| pass | `R6` | an unknown direction is refused |
| pass | `R6` | posting to an account that was never opened is refused |
| pass | `R6` | a posting without a transaction reference is refused |
| pass | `R6` | opening the same account twice is refused |
| pass | `R6` | reading an account that does not exist is refused |
| pass | `I2` | after every refused posting the ledger is unchanged |
| pass | `C4.2` | reconcile() takes exactly ledger, stored balances and a date |
| pass | `C4.2` | no parameter of reconcile() mentions tolerance, threshold or epsilon |
| pass | `C4.2` | the reconciliation module defines no tolerance constant |
| pass | `C4.1` | a clean ledger reconciles with no breaks |
| pass | `C4.1` | and reports zero breaks |
| pass | `C4.3` | a one-dong discrepancy fails the reconciliation |
| pass | `C4.3` | exactly one break is reported |
| pass | `C4.3` | the break names the account |
| pass | `C4.3` | it reports what the ledger says |
| pass | `C4.3` | it reports what the store says |
| pass | `C4.3` | it reports the difference |
| pass | `C4.3` | it names the last entry posted to that account |
| pass | `C4.3` | an account unknown to the ledger is itself a break |
| pass | `C4.3` | the phantom account is named |
| pass | `C4.3` | an account missing from the store is a break, not a skip |
| pass | `C4.3` | it is reported as stored zero |

## integration: ledger

| Result | Ids | Check |
|---|---|---|
| pass | `I3 B3.5` | the commitments sum to the principal |
| pass | `B4.5` | the borrower received exactly the principal at disbursement |
| pass | `R1` | no lender principal passed through a platform account |
| pass | `R1` | the platform's account has no entries at all in this run |
| pass | `I4` | instalment 1: the payment application sums to the amount paid |
| pass | `I5 C2.4` | instalment 1: the distribution sums to the amount paid |
| pass | `C2.4` | instalment 1: one ledger entry per lender, plus the borrower's leg |
| pass | `I4` | instalment 2: the payment application sums to the amount paid |
| pass | `I5 C2.4` | instalment 2: the distribution sums to the amount paid |
| pass | `C2.4` | instalment 2: one ledger entry per lender, plus the borrower's leg |
| pass | `I4` | instalment 3: the payment application sums to the amount paid |
| pass | `I5 C2.4` | instalment 3: the distribution sums to the amount paid |
| pass | `C2.4` | instalment 3: one ledger entry per lender, plus the borrower's leg |
| pass | `I4` | instalment 4: the payment application sums to the amount paid |
| pass | `I5 C2.4` | instalment 4: the distribution sums to the amount paid |
| pass | `C2.4` | instalment 4: one ledger entry per lender, plus the borrower's leg |
| pass | `I4` | instalment 5: the payment application sums to the amount paid |
| pass | `I5 C2.4` | instalment 5: the distribution sums to the amount paid |
| pass | `C2.4` | instalment 5: one ledger entry per lender, plus the borrower's leg |
| pass | `I4` | instalment 6: the payment application sums to the amount paid |
| pass | `I5 C2.4` | instalment 6: the distribution sums to the amount paid |
| pass | `C2.4` | instalment 6: one ledger entry per lender, plus the borrower's leg |
| pass | `I6` | every dong of principal was scheduled |
| pass | `I5` | the lenders hold exactly the total repayable at the end |
| pass | `C4.1` | the borrower's account is empty once the loan is repaid |
| pass | `C2.1` | L1 received more than they committed |
| pass | `C2.1` | L2 received more than they committed |
| pass | `I5` | the lenders' returns sum to the total repaid, with nothing lost to rounding |
| pass | `C4.1` | the run reconciles with no breaks |
| pass | `C4.1` | no balance breaks |
| pass | `I9` | no entry-chain breaks |
| pass | `I2` | the double-entry total across every account is zero |
| pass | `I2` | the external account holds the negative of everything inside |
| pass | `C4.1` | running the scenario twice produces identical balances |
