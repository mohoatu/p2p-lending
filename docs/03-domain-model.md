# Domain model and state machines — v1

Companion to [`01-product-spec.md`](01-product-spec.md) (**R1**–**R6**) and
[`02-user-stories.md`](02-user-stories.md) (**A1**–**C5**).

The premise of this document: most of the regulatory constraints are not
business logic at all. They are **states that must not exist** and
**transitions that must not be reachable**. Written that way they can be
enforced once, at the domain boundary, instead of being re-checked in every
feature by whoever remembers.

---

## 1. Entities

| Entity | Identity | Holds | Notes |
|---|---|---|---|
| **Party** | party_id | kind, legal identifiers | kind ∈ {borrower, lender, platform, partner_bank} |
| **Application** | application_ref | requested amount, term, purpose, state | one active per borrower (A1.4) |
| **CreditCheck** | check_id | application_ref, result, score, queried_at | immutable once written (**R5**) |
| **ExposureEvaluation** | eval_id | borrower, outstanding, requested, cap, verdict, evaluated_at | written at each of the three checkpoints (A3.3) |
| **Loan** | loan_ref | borrower, principal, rate, term, state | created on acceptance, not on approval |
| **Listing** | listing_ref | loan_ref, target, raised, opens_at, closes_at, state | |
| **Commitment** | commitment_id | listing_ref, lender, amount, state, committed_at | ordering by committed_at is load-bearing (C2.2) |
| **Instalment** | loan_ref + seq | due_date, principal, interest, state | generated once, at disbursement |
| **Payment** | payment_id | loan_ref, amount_received, received_at | what arrived, before any interpretation |
| **PaymentApplication** | payment_id + seq | bucket, amount | how the payment was split (C1.1) |
| **Distribution** | distribution_id | payment_id, lender, amount | one per lender per payment |
| **Account** | account_id | owner party, purpose, currency | escrow accounts live at the partner bank |
| **LedgerEntry** | entry_id | account, direction, amount, occurred_at, refs, prev_entry_id | append-only (**R6**) |
| **RiskAcknowledgement** | ack_id | lender, disclosure_version, acknowledged_at | required before first commitment (B2) |

Money is **integer VND** on every one of these. No entity has a decimal or
floating-point money field, which is the cheapest way to make the rule in
spec §5 true rather than merely intended.

### What is deliberately absent

Absences are part of the model, so they are listed rather than left to be
noticed:

- **No `Guarantee`, `Insurance`, or `ProtectionFund` entity.** (**R3**)
- **No `PlatformLoanPosition`.** The platform has accounts for its own fee
  income and nothing else. (**R1**, **R2**)
- **No `CollectionCase`, no `Contact` other than the borrower's own.** (C3.4)
- **No `BalanceOverride`, no `LedgerCorrection` that edits.** A correction is a
  new compensating entry. (**R6**)

A test asserts each of these type names does not exist in the codebase. That
test looks absurd until someone adds one under deadline pressure.

---

## 2. State machines

### 2.1 Application

```
          submit                 assess
draft ──────────────▶ submitted ─────────▶ under_review
                                                │
                   ┌────────────────────────────┼─────────────────────────┐
                   │                            │                         │
         provider down                  checks fail                 checks pass
                   │                            │                         │
                   ▼                            ▼                         ▼
          assessment_blocked         rejected_credit                  approved
                   │                 rejected_exposure_cap               │
          retry    │                                          accept ────┼──── 14 days
                   ▼                                                     │        │
              under_review                                               ▼        ▼
                                                                     accepted  expired
```

**Forbidden, and enforced as such:**

- `under_review → approved` **without** a CreditCheck newer than 30 days
  (**R5**, A2.2)
- `under_review → approved` **without** an ExposureEvaluation with verdict
  `pass` (**R4**, A3)
- `assessment_blocked → approved` directly. It must re-enter `under_review`,
  because provider downtime is not a credit decision (A2.3).
- Any transition **out of** `rejected_*`. A rejected application is terminal; a
  borrower reapplies, creating a new application. This exists so that "fix the
  rejection" is not a thing anyone can do.

### 2.2 Listing

```
                publish              fill to target
draft ─────────────────▶ open ───────────────────────▶ funded ──▶ disbursed
                          │
                          │ window closes below target
                          ▼
                       expired  (all commitments released in full)
```

**Invariants:**

- `raised ≤ target`, always. The transition to `funded` and the acceptance of a
  commitment are a single atomic operation; two concurrent commitments cannot
  both succeed past the target (B4.2).
- `draft → open` re-runs the exposure evaluation (A3.3). A loan approved last
  week may no longer be publishable.
- `expired` releases every commitment at 100%, with **no fee** (B4.3). There is
  no state in which an expired listing's money is anywhere but back with the
  lenders.
- `funded → disbursed` emits a disbursement **instruction** to the partner
  bank. The platform never holds the funds in between (**R1**).

### 2.3 Loan

```
disbursed ──▶ active ──────────────────────▶ settled
                 │  ▲                           ▲
      due date   │  │ payment clears arrears    │ final instalment paid
      passes     ▼  │                           │ or early settlement
                late ──────────────────────────┘
                 │
      30 days    ▼
          default_candidate   ← v1 stops here, by decision
```

**Invariants:**

- `settled` requires outstanding principal, interest, late interest and fees
  all **exactly zero**. Not "within tolerance".
- `late → active` is reachable: arrears cleared returns the loan to normal.
  Lateness is a condition, not a mark.
- `default_candidate` has **no outgoing transition in v1**. The flow genuinely
  stops, which is what "out of scope by decision" means here (spec §4).

### 2.4 Commitment

```
committed ──┬──▶ allocated   (listing funded; lender now holds a share)
            └──▶ released    (listing expired; funds returned in full)
```

Terminal both ways. A commitment is never partially released and never
re-pointed at a different listing.

---

## 3. Invariants, stated as checkable propositions

These hold at every point the system is observed, not just at the end of a
transaction. Each has a test.

| # | Invariant | Rule |
|---|---|---|
| I1 | No Loan, Listing or Commitment references the platform party in a borrower or lender position | **R1**, **R2** |
| I2 | For every Account, the stored balance equals the sum of its LedgerEntries, exactly | **R6** |
| I3 | For every funded Loan, Σ(allocated commitments) = principal | |
| I4 | For every Payment, Σ(its PaymentApplications) = amount_received | C1.1 |
| I5 | For every Payment, Σ(its Distributions) = amount available to distribute | C2.2 |
| I6 | For every Loan, Σ(instalment principal) = principal, and Σ(instalment total) = total repayable | A4.4 |
| I7 | Every approved Application has a CreditCheck and a passing ExposureEvaluation | **R4**, **R5** |
| I8 | For every borrower, Σ(outstanding principal of active loans) ≤ cap | **R4** |
| I9 | Every LedgerEntry's prev_entry_id forms an unbroken chain per account | **R6** |
| I10 | No lender has a Commitment without a RiskAcknowledgement predating it | B2.1 |

**I2 is the one the daily reconciliation job checks (C4), and it is the one
with zero tolerance.** The others are checked on write, because an invariant
you only check nightly is a defect you find a day late.

---

## 4. Where each rule is enforced

The point of concentrating this is that a rule enforced in one place can be
proven in one place.

| Rule | Enforced at | Proven by |
|---|---|---|
| R1, R2 | party-role construction; Loan and Commitment constructors | I1 + a test that attempts the forbidden construction |
| R3 | build-time scan of lender-facing strings; absent entity types | failing build, plus the type-absence test |
| R4 | ExposureEvaluation at three checkpoints | I8 + boundary tests at cap−1, cap, cap+1 |
| R5 | Application state machine guard | I7 + a transition test |
| R6 | LedgerEntry append-only storage; daily job | I2, I9 + a mutation-attempt test |

Five rules, five places. If a sixth place starts enforcing one of them, that is
the signal that the boundary has leaked.

---

## 5. Decisions taken here that could have gone otherwise

Recorded so they can be revisited deliberately:

1. **The Loan is created on acceptance, not on approval.** An approved
   application the borrower never accepts leaves no loan behind. This keeps
   "loans" countable as a real thing rather than as a funnel stage.
2. **Lateness is a loan state, not a flag on an instalment.** A borrower is
   late or not; per-instalment lateness is derivable and does not need storing.
3. **PaymentApplication is separate from Payment.** What arrived and how it was
   interpreted are different facts, and conflating them is how disputes become
   unanswerable.
4. **ExposureEvaluation is persisted, not computed on the fly.** The auditor
   needs to see what the figure was *at the time of the decision*, not what it
   would be recomputed as today.

Decision 4 is the one most likely to be argued with on grounds of redundancy.
It is also the one an auditor will ask for first.
