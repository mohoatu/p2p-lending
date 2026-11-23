# Product specification — v1

A peer-to-peer lending marketplace built to the constraints of Vietnam's
regulatory sandbox for fintech, **Decree 94/2025/NĐ-CP** (in force 1 July 2025).

> **This is a demonstration product.** No real money, no real borrowers, no
> SBV certificate. It exists to show that the rules a licensed operator must
> live under can be expressed as system rules and proven with tests — not left
> in a policy document nobody reads.

---

## 1. The problem

A borrower who cannot get a bank loan and a lender looking for yield both exist.
Connecting them is not hard. **Doing it without the platform quietly becoming a
lender, a guarantor, or a debt collector is hard** — and that is exactly what
the regulator is worried about, because it is what went wrong in Vietnam's
unregulated P2P era.

So the product question is not "can we match borrowers to lenders". It is:

> **Can we make it structurally impossible for the platform to step over the
> line — and prove it to an auditor?**

Everything in this specification follows from that.

---

## 2. Users

| User | What they need | What they must never be able to do |
|---|---|---|
| **Borrower** — individual or household business | Apply once, know quickly if they qualify, see the total cost before accepting, repay without surprises | Borrow beyond the platform's exposure limit |
| **Lender** — individual investor | See real risk information, commit an amount, track repayments, understand that capital is at risk | Be told their capital is protected |
| **Operations** | Review applications, monitor limits, reconcile money daily | Approve a loan that breaches a hard rule |
| **Compliance / auditor** | Reconstruct any loan's full history from records | — |

The fourth user is the one most products forget, and the one the regulator
actually represents.

---

## 3. Regulatory constraints, expressed as system rules

This section is the point of the product. Each rule from Decree 94 becomes a
rule the software enforces, with a test that proves it.

| # | Decree 94 constraint | System rule | How it is proven |
|---|---|---|---|
| R1 | The platform may only **connect information** between borrower and lender | No loan contract may name the platform as a party. The data model has no platform-as-counterparty state to enter. | Test: attempting to create a loan where lender or borrower is the platform entity is rejected |
| R2 | The platform **must not be borrower or lender** on its own platform | The platform's own account cannot hold a lender or borrower role | Test: role assignment rejects the platform entity |
| R3 | The platform **must not provide loan guarantees** | No guarantee, insurance or capital-protection object exists in the model. Lender-facing copy is checked for protection language. | Test: a vocabulary check over lender-facing strings fails on "guaranteed", "bảo đảm vốn", "risk-free" and similar |
| R4 | **Maximum outstanding debt per borrower** must be controlled | A hard limit evaluated before a listing can be funded; it blocks, it does not warn | Test: funding that would breach the cap is refused, at the boundary and one unit either side |
| R5 | Must be able to **query CIC** (national credit information) | Credit assessment has an explicit CIC step with a recorded result and timestamp; stubbed in the demo, with the interface real | Test: an application cannot reach "approved" without a recorded credit-check result |
| R6 | **Annual independent audit** | Every money-affecting event is appended to an immutable ledger; balances are derived from it, never edited | Test: the ledger reconciles against derived balances for every account, on every run |
| R7 | Trial period is **at most 2 years** | Not a system rule — a roadmap fact. Recorded here so it is not forgotten. | — |

**Money never rests with the platform.** Lender funds sit in an escrow account
at a partner bank; the platform instructs movements and records them, but holds
nothing. This is a direct consequence of R1 and R2 rather than a separate
choice, and it is the single most important architectural decision in the
product.

---

## 4. Scope

### In scope for v1

- Borrower application, KYC capture, credit assessment (CIC stubbed)
- Risk grade and an interest rate derived from it
- Loan listing, lender commitment, funding to target
- Disbursement instruction, repayment schedule generation
- Repayment recording, early settlement, late handling up to day 30
- Immutable ledger and daily reconciliation
- Exposure limit enforcement
- Operations console and an auditor's view of any loan's full history

### Explicitly out of scope for v1

Stated so the boundary is a decision rather than an omission:

- **Real money movement.** Escrow is an interface with a simulated
  implementation.
- **Real KYC/eKYC vendor** and **real CIC connection** — interfaces only.
- **Secondary market** (lenders selling loan parts). Interesting, and a
  regulatory question of its own.
- **Collections beyond day 30.** Deliberate: debt collection is where
  Vietnam's unregulated P2P operators did the most damage, and it needs its own
  policy work before any code.
- **Mobile apps.** Web only.

---

## 5. Money arithmetic — the rules that cause most real defects

From direct experience building the comparison tooling in `migration-verify`:
money differences of one cent are where migrations and ledgers go wrong, and
they come from unstated rounding rules. So they are stated here.

- All monetary values are **integer VND**. No floating point anywhere.
- Interest is computed on **actual outstanding principal**, daily accrual,
  365-day year.
- Each instalment is rounded to the nearest đồng, **half up**.
- The **final instalment absorbs the residue** so the instalments sum exactly
  to principal plus total interest. This must be stated, because a report
  showing "the instalment amount" is ambiguous otherwise — a lesson learned the
  expensive way.
- Partial payments apply in order: **fees → late interest → interest →
  principal**. The order is a business decision and is recorded here, not left
  to the code.

---

## 6. Metrics

What the product is measured by, and what it is deliberately not.

| Metric | Why |
|---|---|
| Application-to-funded conversion | the core funnel |
| Time from application to disbursement | the borrower's actual experience |
| Fill rate of listings | whether lender supply matches borrower demand |
| Portfolio at risk (PAR 30) | the number that matters to lenders |
| Reconciliation breaks per day | **target zero**; any break is an incident |
| Rule-block rate (R4 exposure cap) | how often the hard limit actually bites |

**Not metrics:** total loans listed, registered users, app downloads. They go up
whatever happens, which is what makes them comfortable and useless.

---

## 7. Risks

| # | Risk | Mitigation |
|---|---|---|
| 1 | Product drifts into acting as lender or guarantor under commercial pressure | R1–R3 enforced in the model and tested; the tests fail loudly rather than warning |
| 2 | Lenders believe capital is protected | R3 vocabulary check; risk disclosure required before first commitment |
| 3 | Rounding differences accumulate into a ledger break | Integer arithmetic, residue rule stated, daily reconciliation with zero tolerance |
| 4 | Over-indebtedness of borrowers | R4 exposure cap plus CIC check |
| 5 | Demo is mistaken for an operating service | Stated at the top of every document and on the interface itself |

---

## 8. Open questions

Recorded rather than guessed:

1. What is the right exposure cap per borrower, and is it set by the platform
   or by the regulator?
2. Does the lender need to be a qualified investor, and is there a per-lender
   cap?
3. How is a defaulted loan resolved when the platform may not collect?
4. Does a secondary market fall inside or outside the sandbox scope?

Questions 1 and 3 are the ones a real operator must answer before writing code.
