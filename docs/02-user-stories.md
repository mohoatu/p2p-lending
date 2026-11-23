# User stories and acceptance criteria — v1 core flows

Companion to [`01-product-spec.md`](01-product-spec.md). Rule references
(**R1**–**R6**) point at section 3 of that document.

**How acceptance criteria are written here.** Each is a statement that is either
true or false when the system is inspected — not a description of a feeling.
Where a number appears it is a decision, not an illustration; where a number is
still open it is marked `[OPEN]` and listed in section 4.

Three flows cover v1. Everything else in the product exists to serve them.

---

## Flow A — Borrower: application to approval

### A1 — Submit an application

> **As a** borrower
> **I want** to apply for a loan in one sitting
> **So that** I find out whether I qualify without a branch visit

**Acceptance criteria**

1. The application captures: amount requested, term in months, purpose,
   national ID, monthly income, existing debt obligations.
2. Requested amount is between 5,000,000 and 100,000,000 VND inclusive.
   Outside that range the form is rejected with the boundary stated in the
   message. `[OPEN-1: upper bound]`
3. Term is one of 3, 6, 12, 18, 24 months. No free-text term.
4. An application cannot be submitted twice by the same national ID while an
   earlier one is in `submitted`, `under_review` or `approved` state.
5. On submission the borrower sees an application reference and the state
   `submitted`. No cost figures are shown yet, because none have been computed.

### A2 — Credit assessment with a recorded CIC result (**R5**)

> **As** operations
> **I want** every approval to carry a credit-check result
> **So that** the file withstands audit

**Acceptance criteria**

1. The assessment step calls the credit-information interface and stores:
   result code, score, query timestamp, and the identifier of the query.
2. An application **cannot** transition to `approved` unless a credit-check
   record exists and its timestamp is within 30 days. The transition is
   refused; it is not warned about.
3. If the credit-information provider is unavailable, the application moves to
   `assessment_blocked`, not to `approved` and not to `rejected`. Provider
   downtime is not a credit decision.
4. In the demonstration build the provider is a stub. The stub is selected by
   configuration, and the interface it implements is the real one.

### A3 — Exposure cap blocks, it does not warn (**R4**)

> **As** the regulator's interest in the system
> **I want** a borrower's total outstanding debt on the platform to be capped
> **So that** the platform cannot contribute to over-indebtedness

**Acceptance criteria**

1. Before approval the system computes the borrower's **total outstanding
   principal** across all their active loans, plus the amount now requested.
2. If that total exceeds the cap, the application is set to
   `rejected_exposure_cap` with the computed figures recorded.
3. The check is evaluated at three points and behaves identically at each:
   approval, listing publication, and each lender commitment. A loan can be
   approved and still be blocked later if the borrower's position changed in
   between.
4. Tests exercise the boundary: cap minus 1 đồng passes, exactly the cap
   passes, cap plus 1 đồng is refused. `[OPEN-1: cap value]`
5. There is no override. No operations role, no configuration flag.

### A4 — Price the loan and show the total cost

> **As a** borrower
> **I want** to see what the loan will cost me in total before I accept
> **So that** I am not surprised by the schedule

**Acceptance criteria**

1. On approval the system produces a risk grade and derives an annual interest
   rate from a published grade-to-rate table. The table is data, not code.
2. The borrower is shown, before accepting: principal, annual rate, term,
   **total amount repayable**, instalment amount, and all fees itemised.
3. The full repayment schedule is shown — every instalment row, with date,
   principal, interest and remaining balance.
4. The instalments in the displayed schedule **sum exactly** to total repayable.
   No row is rounded independently of the total; the final instalment absorbs
   the residue (spec §5).
5. Accepting is an explicit action by the borrower. There is no pre-ticked box.

---

## Flow B — Lender: listing to funded

### B1 — Browse listings with honest risk information (**R3**)

> **As a** lender
> **I want** to see what I am actually taking on
> **So that** I can decide, rather than be sold to

**Acceptance criteria**

1. Each listing shows: amount, term, rate, risk grade, grade definition, the
   borrower's purpose category, and the funding progress.
2. Borrower identity is **not** shown. Listings carry a reference, not a name.
3. Every listing page carries the capital-at-risk statement, visible without
   scrolling or expanding anything.
4. A build-time check scans all lender-facing strings and **fails the build**
   on protection vocabulary — "guaranteed", "bảo đảm vốn", "an toàn tuyệt đối",
   "risk-free", "capital protected" and the agreed list. A new banned term is
   added to the list, not argued about in review.
5. No listing displays a historical return figure, because the platform has no
   history. An empty state says so.

### B2 — First-time lender acknowledges the risk

> **As** the system
> **I want** a lender to have read the risk disclosure before their first đồng
> **So that** consent is recorded rather than assumed

**Acceptance criteria**

1. A lender's first commitment is refused unless a risk-acknowledgement record
   exists for that lender, with version and timestamp.
2. The acknowledgement names the specific facts: capital may be lost in full,
   there is no deposit insurance, the platform does not guarantee repayment,
   and the platform is not a party to the loan (**R1**).
3. When the disclosure text changes, its version increments and acknowledgement
   is required again at the next commitment.

### B3 — Commit funds into escrow, never to the platform (**R1**, **R2**)

> **As a** lender
> **I want** my money to go to the loan, not to the platform's balance sheet
> **So that** platform failure is not my exposure

**Acceptance criteria**

1. A commitment moves funds from the lender's escrow balance at the partner
   bank to a committed state. The platform's own accounts are never credited
   or debited with lender principal at any point in the flow.
2. The data model has no state in which the platform entity holds a `lender` or
   `borrower` role. Attempting to construct one is rejected at the domain
   boundary, with a test proving it (**R2**).
3. Commitment amount is at least 500,000 VND and a multiple of 100,000 VND.
   `[OPEN-2]`
4. A commitment that would take the listing past 100% of target is refused;
   the lender is told the remaining amount.
5. Commitments are recorded in the immutable ledger at the moment they are
   accepted (**R6**).

### B4 — Funding completes or expires

> **As a** borrower
> **I want** a definite answer within a known window
> **So that** I can look elsewhere if it does not fund

**Acceptance criteria**

1. A listing has a funding window of 14 days. `[OPEN-3]`
2. At 100% the listing moves to `funded` and no further commitments are
   accepted. The transition is atomic — concurrent commitments cannot push a
   listing above target.
3. If the window closes below 100%, the listing moves to `expired` and **every
   committed amount is released back to the lender's escrow balance in full**.
   No fee is taken on an expired listing.
4. Partial funding is never disbursed. `[OPEN-4: is a partial-funding option
   worth having?]`
5. On `funded`, disbursement is instructed to the partner bank and recorded.
   The platform does not hold the money in between.

---

## Flow C — Repayment and reconciliation

### C1 — Record a repayment

> **As a** borrower
> **I want** my payment applied in a way I can check
> **So that** my balance is never a mystery

**Acceptance criteria**

1. A payment is applied in the order **fees → late interest → interest →
   principal** (spec §5). The application is recorded line by line, not as a
   single net figure.
2. The borrower can see, for any payment: what was received, how it was split,
   and the resulting outstanding balance.
3. A payment larger than the amount due is accepted and reduces principal, with
   the schedule recalculated and shown.
4. Early settlement quotes the exact figure to clear the loan **today**,
   including interest accrued to today and no interest beyond it.
5. All arithmetic is integer VND. A test asserts no floating-point type appears
   in any money path.

### C2 — Distribute to lenders pro rata

> **As a** lender
> **I want** my share of each repayment
> **So that** my return matches my contribution**

**Acceptance criteria**

1. Each repayment is split across lenders in proportion to committed principal.
2. The split sums **exactly** to the amount received. The residue from rounding
   is allocated by a stated deterministic rule — largest remainder, ties broken
   by earliest commitment — not dropped and not duplicated.
3. The rule is tested with an adversarial case: 3 lenders, an amount not
   divisible by 3, verifying the parts sum to the whole.
4. Distribution is a ledger entry per lender (**R6**), never a balance edit.

### C3 — Late handling to day 30

> **As** operations
> **I want** lateness handled by rule
> **So that** nobody improvises with a borrower in difficulty

**Acceptance criteria**

1. Day 1 overdue: state `late`, lenders see it on the listing, late interest
   begins accruing at the stated rate. `[OPEN-5: rate]`
2. Day 5 and day 15: a reminder is recorded as sent. The content is
   informational. No threat, no third party contacted, no reference to the
   borrower's contacts or employer.
3. Day 30: state `default_candidate`, and the flow stops there in v1. What
   happens next is out of scope by decision (spec §4) and is open question 3.
4. There is no system capability to contact anyone other than the borrower
   about the borrower's debt. This is an absent feature, asserted by test.

### C4 — Daily reconciliation with zero tolerance (**R6**)

> **As an** auditor
> **I want** the ledger and the balances to agree, every day
> **So that** a discrepancy is an incident rather than a discovery

**Acceptance criteria**

1. A daily job derives every account balance from the ledger and compares it to
   the stored balance.
2. Tolerance is **zero đồng**. There is no "acceptable difference" threshold,
   for the reason set out in spec §5.
3. Any mismatch produces a reconciliation break record naming the account, the
   expected and actual figures, and the last ledger entry — and the day's
   reconciliation is marked failed.
4. The ledger is append-only. There is no update or delete path to a posted
   entry; a correction is a new compensating entry referencing the original.
5. A test attempts to mutate a posted ledger entry and asserts it is refused.

### C5 — Reconstruct any loan's full history

> **As an** auditor
> **I want** one place that shows everything that happened to a loan
> **So that** I do not have to ask an engineer

**Acceptance criteria**

1. Given a loan reference, the system renders every event in order with
   timestamps: application, credit check, exposure evaluation, approval,
   pricing, listing, each commitment, disbursement, each repayment and its
   split, each distribution, each state change.
2. The view is generated from the ledger and the event records, not assembled
   by hand.
3. It is exportable as a file.
4. It is reachable by an auditor role without engineering assistance — that is
   the actual requirement, and the test of it is that nobody runs a query.

---

## 4. Open questions carried by these stories

| Ref | Question | Who decides | Blocks |
|---|---|---|---|
| OPEN-1 | Exposure cap per borrower, and the maximum loan amount — platform policy or regulator-set? | legal | A1, A3 |
| OPEN-2 | Minimum lender commitment and increment | product | B3 |
| OPEN-3 | Funding window length | product | B4 |
| OPEN-4 | Allow partial funding to disburse? | product | B4 |
| OPEN-5 | Late interest rate, and whether it is capped by law | legal | C3 |

OPEN-1 and OPEN-5 are legal questions and are not guessed. The others are
product decisions with a default already in the criteria above, which can be
changed without changing the design.

---

## 5. What is deliberately not here

- No notification or messaging stories. Reminders in C3 are recorded, and how
  they are delivered is an implementation detail in v1.
- No lender portfolio analytics. A lender can see their loans; a dashboard
  comes after the core flows are correct.
- No admin user management. Roles exist; administering them does not.

Each of these is an omission by decision, so that the absence of a story is not
read as an oversight.
