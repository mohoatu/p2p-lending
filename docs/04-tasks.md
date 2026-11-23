# Implementation tasks — v1

Derived from [`01-product-spec.md`](01-product-spec.md),
[`02-user-stories.md`](02-user-stories.md) and
[`03-domain-model.md`](03-domain-model.md). Process and definitions live in
[`../CLAUDE.md`](../CLAUDE.md).

**How to read a task.** Each has the spec identifiers it implements, a
**done-when** that is observable rather than felt, and its dependencies. A task
is not done when the code exists; it is done when the named tests pass and the
traceability gate accepts the identifiers it claims.

Size is relative: **S** a sitting, **M** a day, **L** more than a day and a
candidate for splitting if it stays L once started.

## Progress

| Phase | Tasks | State |
|---|---|---|
| 0 — the gate | T01, T02 | **done** |
| 1 — money | T03–T06 | **done** |
| 2 — the ledger | T07, T08 | **done** |
| 3 — parties and rules | T09–T11 | next |
| 4 — application to approval | T12–T15 | |
| 5 — listing to funded | T16–T18 | |
| 6 — repayment and audit | T19–T22 | |
| 7 — converge | T23–T25 | |

308 checks passing; the traceability gate reports 25 of 75 documented
requirements covered. The authoritative version of that figure is
`evidence/traceability.md`, which is regenerated on every evidence run — if
this table and that file ever disagree, the file is right.

---

## Phase 0 — The gate comes first

Building the traceability gate before the code is deliberate. A gate added at
the end only ever reports what was already built; a gate present from the start
makes the gap visible on every run, and the gap shrinking is the progress
report.

### T01 — Traceability gate, in report-only mode · S

Parse `docs/02` and `docs/03` for identifiers (`A1.4`, `B4.3`, `C2.2`, `I7`,
`R5`). Parse `tests/` for identifiers claimed. Print three lists: covered,
uncovered, and **claimed-but-not-in-docs**.

- **Implements:** CLAUDE.md "Traceability"
- **Done when:** running it on the empty test suite lists every identifier in
  the docs as uncovered, and the count matches a hand count of the documents.
- **Depends on:** nothing

Report-only until T19. The uncovered list is expected to be long, and it is the
backlog in a second form — if it ever disagrees with this file, this file is
wrong.

### T02 — Test runner skeleton · S

`tests/run.py` discovers and runs the suites, counts checks, exits non-zero on
any failure. Vanilla; no pytest. stdout reconfigured to UTF-8 so the Vietnamese
banned-vocabulary strings survive a cp1252 console (CLAUDE.md "Traps").

- **Done when:** a deliberately failing placeholder check makes the exit code 1,
  and a run prints identifiers alongside results.
- **Depends on:** nothing

---

## Phase 1 — Money, before anything that touches it

Nothing above this layer can be trusted until this layer is exact. It is also
the part that is pure, so it is the cheapest to get right.

### T03 — Money type and rounding · S

Integer VND throughout. Half-up rounding. A guard that rejects float at the
boundary rather than converting it.

- **Implements:** spec §5, CLAUDE.md constitution 4
- **Done when:** unit tests cover half-up at `.5` in both directions, negative
  amounts, and that passing a `float` or `Decimal` into a money field raises.
- **Depends on:** T02

### T04 — Repayment schedule generation · M

Instalments from principal, rate, term. Daily accrual on outstanding principal,
365-day year. **The final instalment absorbs the residue.**

- **Implements:** A4.3, A4.4, I6
- **Done when:** for a spread of principals and terms including ones that do not
  divide evenly, `Σ(instalment principal) == principal` and `Σ(instalment total)
  == total repayable`, exactly, with no case excused.
- **Depends on:** T03

### T05 — Payment application order · S

Split a received amount across **fees → late interest → interest → principal**,
recorded line by line. Overpayment reduces principal. Early settlement quotes
interest to today and not one đồng beyond.

- **Implements:** C1.1, C1.3, C1.4, I4
- **Done when:** `Σ(applications) == amount_received` for every case, including
  a payment smaller than the fee, and a payment larger than the whole loan.
- **Depends on:** T03

### T06 — Pro-rata distribution with a stated residue rule · M

Split across lenders by committed principal. Residue by largest remainder, ties
broken by earliest commitment.

- **Implements:** C2.1, C2.2, C2.3, I5
- **Done when:** the adversarial case passes — 3 lenders, an amount not
  divisible by 3 — plus a randomised property check over many splits asserting
  the parts always sum to the whole. The random seed is fixed and recorded.
- **Depends on:** T03

---

## Phase 2 — The ledger

### T07 — Append-only ledger · M

Entries carry account, direction, amount, timestamp, references, and
`prev_entry_id`. **No update or delete path exists in the type.**

- **Implements:** R6, I9, CLAUDE.md "Boundaries"
- **Done when:** a negative test attempting to mutate a posted entry fails to
  find a way to do so, and the per-account chain is unbroken across a few
  hundred entries.
- **Depends on:** T03

### T08 — Balances and reconciliation · M

Balances derived from the ledger. A reconciliation pass comparing derived to
stored, **tolerance zero**, producing break records naming account, expected,
actual and last entry.

- **Implements:** R6, I2, C4.1–C4.3
- **Done when:** a clean ledger reconciles to zero breaks; a deliberately
  corrupted stored balance produces exactly one break with the right figures;
  and no configuration can set a non-zero tolerance, asserted by test.
- **Depends on:** T07

---

## Phase 3 — Parties and the rules that bind them

### T09 — Party roles, with the platform excluded · S

Party kinds. Construction of a Loan or Commitment naming the platform in a
borrower or lender position is refused at the domain boundary.

- **Implements:** R1, R2, I1
- **Done when:** the negative test attempting that construction asserts refusal,
  and the absence test confirms no `PlatformLoanPosition` type exists.
- **Depends on:** T02

### T10 — Absence tests · S

Assert that `Guarantee`, `Insurance`, `ProtectionFund`, `CollectionCase`,
`BalanceOverride` and any editing `LedgerCorrection` do not exist in `src/`.

- **Implements:** R3, R6, `docs/03` §1, C3.4
- **Done when:** the test passes on the current tree, **and** fails when a
  throwaway class with one of those names is added — verified once, by actually
  adding it and removing it again.
- **Depends on:** T02

The verification step is the whole point. An absence test nobody has seen fail
is not known to work.

### T11 — Banned vocabulary scan · S

Scan lender-facing strings for protection language, in English and Vietnamese.
Fails the run, not warns.

- **Implements:** R3, B1.4
- **Done when:** a string containing `bảo đảm vốn` anywhere in a lender-facing
  surface turns the run red, and the term list is a data file an engineer adds
  to rather than argues about.
- **Depends on:** T02

---

## Phase 4 — Flow A: application to approval

### T12 — Application state machine · M

States and transitions per `docs/03` §2.1, with the forbidden ones unreachable
rather than merely unused.

- **Implements:** A1.4, R5 guard, `docs/03` §2.1
- **Done when:** negative tests confirm `under_review → approved` without a
  credit check is refused, `assessment_blocked → approved` directly is refused,
  and **no transition out of `rejected_*` exists**.
- **Depends on:** T02, T09

### T13 — Credit information adapter and its stub · M

Real interface, stub implementation selected by configuration. Result recorded
with timestamp and query identifier, immutable once written.

- **Implements:** R5, A2.1–A2.4
- **Done when:** approval with a check older than 30 days is refused at 30 days
  plus one; provider failure yields `assessment_blocked`, never `rejected`.
- **Depends on:** T12

### T14 — Exposure evaluation at three checkpoints · M

Computed and **persisted** at approval, listing publication, and each
commitment. No override anywhere.

- **Implements:** R4, A3.1–A3.5, I8
- **Done when:** boundary tests pass at cap−1, cap, cap+1 at **each** of the
  three checkpoints — nine cases, not three — and a test confirms no code path
  can bypass the check.
- **Depends on:** T12

### T15 — Pricing and borrower acceptance · M

Grade-to-rate table as data. Total cost and full schedule shown before
acceptance. Acceptance explicit; the Loan is created here, not at approval.

- **Implements:** A4.1–A4.5, `docs/03` §5.1
- **Done when:** the displayed instalments sum exactly to total repayable, and
  an approved application left unaccepted for 14 days expires leaving no Loan
  behind.
- **Depends on:** T04, T12

---

## Phase 5 — Flow B: listing to funded

### T16 — Listing state machine and atomic funding · L

Publication re-runs exposure. Commitments accepted atomically; `raised ≤ target`
always holds.

- **Implements:** B3.4, B4.1, B4.2, A3.3
- **Done when:** a concurrency test fires simultaneous commitments at a listing
  with room for one and asserts exactly one succeeds — run repeatedly, not once.
- **Depends on:** T08, T14

### T17 — Risk acknowledgement before the first commitment · S

Versioned disclosure; acknowledgement recorded; re-required on version change.

- **Implements:** B2.1–B2.3, I10
- **Done when:** a first commitment without an acknowledgement is refused, and
  bumping the disclosure version re-requires it.
- **Depends on:** T16

### T18 — Expiry releases everything, and escrow holds the money · M

Below target at window close: every commitment released at 100%, **no fee**.
Funded: a disbursement instruction to the partner-bank adapter. The platform's
accounts are never credited with lender principal.

- **Implements:** B4.3, B4.5, R1, I3
- **Done when:** after an expiry, every lender's escrow balance is exactly what
  it was before committing — asserted by ledger reconciliation, not by reading
  a balance field.
- **Depends on:** T16

---

## Phase 6 — Flow C: repayment, lateness, audit

### T19 — Loan state machine and repayment recording · M

`active ↔ late`, settlement requiring everything at exactly zero.

- **Implements:** C1.2, `docs/03` §2.3
- **Done when:** `late → active` on clearing arrears is reachable and tested;
  `settled` with one đồng outstanding is refused.
- **Depends on:** T05, T07, T18

### T20 — Distribution to lenders · S

One ledger entry per lender per payment. Never a balance edit.

- **Implements:** C2.4, I5
- **Done when:** after a full loan lifecycle the ledger reconciles to zero
  breaks across every lender account.
- **Depends on:** T06, T19

### T21 — Late handling to day 30 · M

Day 1 late interest accrues; day 5 and 15 reminders recorded; day 30
`default_candidate`, terminal.

- **Implements:** C3.1–C3.4
- **Done when:** a negative test confirms **there is no code path that contacts
  anyone other than the borrower**, and `default_candidate` has no outgoing
  transition.
- **Depends on:** T19

### T22 — Audit trail · M

Every event for a loan, in order, generated from the ledger and event records,
exportable, reachable by an auditor role.

- **Implements:** C5.1–C5.4
- **Done when:** an integration test runs a full lifecycle and asserts the trail
  contains every event type in `docs/02` C5.1, in order — **and the assertion is
  written from the document, not from the output.**
- **Depends on:** T20, T21

That last clause is the difference between a test and a snapshot of a bug.

---

## Phase 7 — Converge

### T23 — Full-lifecycle integration run · M

Multiple borrowers, multiple lenders, listings that fund and listings that
expire, loans that settle and loans that go late. Ends in reconciliation.

- **Implements:** C4, I2–I5
- **Done when:** zero breaks, and the run is deterministic — same seed, same
  output, verified by running it twice and comparing.
- **Depends on:** T22

### T24 — Flip the traceability gate to enforcing · S

- **Implements:** CLAUDE.md "Traceability"
- **Done when:** the uncovered list is empty, the claimed-but-undocumented list
  is empty, and the gate exits non-zero if either regrows.
- **Depends on:** T23

### T25 — Evidence generation · M

`tests/run.py --evidence` writes `results.md`, `traceability.md`,
`reconciliation.md`, `run.txt` and `screenshots/`.

- **Implements:** CLAUDE.md "Evidence"
- **Done when:** `evidence/` is readable by someone who has not seen the code —
  the test of that is whether the traceability matrix alone answers "what proves
  the platform cannot be a lender?"
- **Depends on:** T24

---

## Ordering, and what it costs to reorder

```
T01 T02  ──▶  T03 ──▶ T04 T05 T06
                │
                └──▶ T07 ──▶ T08
T09 T10 T11 ─────────┐
                     ▼
            T12 ──▶ T13 T14 ──▶ T15
                             │
                             ▼
                    T16 ──▶ T17 T18 ──▶ T19 ──▶ T20 T21 ──▶ T22
                                                              │
                                                              ▼
                                                    T23 ──▶ T24 ──▶ T25
```

Phases 0 and 1 are not negotiable in order. Everything downstream inherits the
money layer, and a rounding rule changed after Phase 5 invalidates every
reconciliation assertion written in between — which is not a refactor, it is a
re-proof.

## Not in this list, on purpose

No UI tasks. The product is the domain and its proofs; a presentation layer
would be the natural Phase 8, and it is deliberately not started first, because
a screen is the easiest thing to mistake for progress.
