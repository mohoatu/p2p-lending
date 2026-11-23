# CLAUDE.md — working notes for agents on this repo

Read this before writing any code. It is short on purpose; the long version is
in [`docs/`](docs/), and the specification is the authority, not this file.

This project follows **Spec-Driven Development** in the sense of
[github/spec-kit](https://github.com/github/spec-kit): the specification is the
artefact, and code is derived from it. Spec Kit's CLI is not installed here —
the repo is small enough that its conventions are adopted directly, and
`docs/01`–`03` already hold what `/speckit-specify` and `/speckit-plan` would
have produced. If the CLI is added later, the section layout below is already
compatible.

---

## What this project is

A **peer-to-peer lending marketplace** designed to Vietnam's fintech regulatory
sandbox, **Decree 94/2025/NĐ-CP**. A demonstration product: no real money, no
real borrowers, no State Bank certificate.

The thesis is in `docs/01-product-spec.md` §3 and is the reason the repo exists:
**regulatory constraints are not business logic — they are states that must not
exist and transitions that must not be reachable.** Code that re-checks a rule
in a feature handler has already lost the argument.

---

## Constitution — the principles that outrank convenience

Spec Kit calls this the constitution: decided once, not re-litigated per task.

1. **The spec is the authority.** Where code and `docs/` disagree, the code is
   wrong — or the spec is changed first, deliberately, and the code follows.
   Never the reverse order, and never silently.
2. **Every rule is enforced in exactly one place.** Five rules, five places
   (`docs/03` §4). A sixth place enforcing an existing rule is the signal that
   the boundary has leaked, and is a defect even if the tests pass.
3. **Refusal over approximation.** When the system cannot do something
   correctly, it refuses and says so. It does not warn, does not clamp, does not
   pick a default. A blocked exposure cap is a refusal; a provider outage is
   `assessment_blocked`, not a credit decision.
4. **Integer VND, everywhere, always.** No float, no `Decimal` in money paths.
   Rounding residue goes where the spec says it goes (§5), not where the last
   line of code happens to put it.
5. **Zero tolerance means zero.** Reconciliation does not have an acceptable
   difference. A tolerance is a place for a defect to live.
6. **Absences are features.** The entities that must not exist (`docs/03` §1)
   are asserted absent by test. That test looks absurd until someone adds one
   under deadline pressure.
7. **Vanilla Python, no dependencies.** Standard library only, for tests too.
   A dependency in a system handling money is a security review; adding one
   needs a reason that outweighs that.

---

## The loop

Adapted from Spec Kit's `specify → plan → tasks → implement → converge`.
Steps 1–3 are **done** for v1; the work now is 4 and 5.

| Step | Spec Kit equivalent | Here | State |
|---|---|---|---|
| 1 | `/speckit-constitution` | this file, above | done |
| 2 | `/speckit-specify` | `docs/01-product-spec.md`, `docs/02-user-stories.md` | done |
| 3 | `/speckit-plan` | `docs/03-domain-model.md` | done |
| 4 | `/speckit-tasks` | `docs/04-tasks.md` | **next** |
| 5 | `/speckit-implement` | `src/` + `tests/` | not started |
| 6 | `/speckit-converge` | `evidence/` + the traceability gate | not started |

**Convergence here has a precise meaning:** every acceptance criterion in
`docs/02` and every invariant in `docs/03` is referenced by at least one passing
test, and the traceability gate agrees. Not "the tests are green" — green with a
criterion nobody tested is not converged.

---

## Traceability — how "code follows the spec" is made checkable

Claiming it is worthless. So:

- **Every test carries the identifier it proves**, in its name and in its
  recorded result: `I2`, `A3.4`, `B4.3`, `C2.2`, `R5`. One test may carry
  several.
- **Every module states what it implements** in its docstring, by identifier.
- **`tests/traceability.py` is a test like any other.** It parses `docs/02` and
  `docs/03` for identifiers, parses the test suite for the identifiers claimed,
  and **fails on any criterion or invariant with no test**. It also fails on a
  test claiming an identifier that does not exist in the docs, which is how
  renames get caught.

The gate is deliberately strict in both directions. A one-way check lets the
spec drift ahead of the code silently, which is the failure this whole repo is
an argument against.

---

## Tests — three kinds, and the third matters most

| Suite | File | What it covers |
|---|---|---|
| **Unit** | `tests/test_unit_*.py` | Money arithmetic, schedule generation, pro-rata split, state-machine guards. Pure — no I/O, no clock, no randomness. |
| **Integration** | `tests/test_integration_*.py` | Whole flows A → B → C against a real in-memory store, ending in a ledger reconciliation that must come out at **0 đồng**. |
| **Negative** | `tests/test_negative_*.py` | Attempts the forbidden and asserts refusal. |
| **Traceability** | `tests/traceability.py` | The gate above. |

**The negative suite is the product.** For this system, "it did the right thing"
is less interesting than "it would not do the wrong thing". It must include, at
minimum: approval without a credit check (**R5**), funding past the exposure cap
at the boundary (**R4**), mutating a posted ledger entry (**R6**), constructing
the platform as a lender or borrower (**R1**, **R2**), protection vocabulary in
lender-facing strings (**R3**), a commitment from a lender with no risk
acknowledgement (B2.1), and a transition out of `rejected_*` or out of
`default_candidate` (`docs/03` §2).

Boundary tests are written at **three points** — one below, exactly on, one
above. A cap tested only at "way over" is not tested.

`tests/run.py` runs everything and is the only command that matters before a
commit.

---

## Evidence

Running the tests is not the deliverable; **being able to show what was proven
is**. `tests/run.py --evidence` writes to `evidence/`:

| File | Contents |
|---|---|
| `evidence/results.md` | Every check, its identifier, pass or fail, with totals per suite |
| `evidence/traceability.md` | The spec-to-test matrix: each criterion and invariant, and which tests cover it |
| `evidence/reconciliation.md` | The closing ledger reconciliation from the integration run, per account |
| `evidence/run.txt` | Raw console output, with Python version, platform and timestamp |
| `evidence/screenshots/` | Screen captures of the run |

`evidence/` is **committed**. It is the thing that gets opened in an interview,
so it is written to be read by someone who has not seen the code.

Regenerate it in the same commit as any change to `src/`, `tests/` or `docs/`.
Stale evidence is worse than none, because it is believed.

---

## Layout

```
CLAUDE.md          This file — constitution and process
README.md          Public front page
docs/              01 spec · 02 user stories · 03 domain model · 04 tasks
src/               The implementation. Pure domain core, adapters at the edge
tests/             unit · integration · negative · traceability · run.py
evidence/          Generated, and committed. See above
```

Boundaries worth respecting:

- **`src/domain/` knows nothing about storage, time, or the outside world.**
  The clock and the store are passed in. This is what makes the state machine
  testable without a fixture, and it is not negotiable for a money system.
- **Adapters (`src/adapters/`) hold the stubs** — credit information, partner
  bank escrow. The stub is selected by configuration; the interface it
  implements is the real one (A2.4). Do not let a stub's convenience shape the
  interface.
- **The ledger is append-only in the type, not by discipline.** There is no
  update path to expose. If one appears, I6/I9 are no longer being enforced in
  one place (constitution §2).

---

## Commands

All from the repo root. No dependencies.

```bash
python tests/run.py              # everything — must be green before any commit
python tests/run.py --evidence   # the same, and regenerate evidence/
python tests/traceability.py     # the spec-to-test gate alone
```

---

## Traps

- **Changing an identifier in `docs/02` or `docs/03` breaks the traceability
  gate.** That is the gate working. Fix the tests, do not relax the gate.
- **The open questions are open on purpose.** `docs/02` §4 lists five, two of
  them legal (exposure cap, late interest rate). Code uses the stated default
  and names it as a default. Do not quietly promote a default into a decision.
- **Vietnamese text appears in the banned-vocabulary list** (`bảo đảm vốn`,
  `an toàn tuyệt đối`). Source files are UTF-8; on Windows the console is
  cp1252, so anything printing those strings must reconfigure stdout — the same
  bug that cost a day in `migration-verify`.
- **Documents cross-reference each other by identifier constantly.** Renaming a
  section means fixing `docs/`, the tests, and `evidence/`.
- **Never rewrite `main` or force-push.** Work on `development`.
