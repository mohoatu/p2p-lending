# p2p-lending

A peer-to-peer lending marketplace designed to Vietnam's fintech regulatory
sandbox, **Decree 94/2025/NĐ-CP**.

> **Demonstration product.** No real money, no real borrowers, no State Bank
> certificate, not an operating service.

---

## Why this exists

Matching a borrower to a lender is not the hard part. Doing it without the
platform quietly becoming a lender, a guarantor, or a debt collector is — and
that is precisely what went wrong in Vietnam's unregulated P2P era, and what
Decree 94 is written to prevent.

So the question this repository answers is:

> **Can the rules a licensed operator must live under be expressed as system
> rules, and proven to an auditor?**

Six constraints from the decree are mapped to enforced, testable system rules.
A platform that cannot be a counterparty is not a policy promise here; it is a
state the data model has no way to enter, with a test that proves it.

## Documents

| Document | What it covers |
|---|---|
| [`docs/01-product-spec.md`](docs/01-product-spec.md) | Problem, users, the Decree 94 constraint-to-rule mapping, scope, money arithmetic, metrics, risks |
| [`docs/02-user-stories.md`](docs/02-user-stories.md) | Acceptance criteria for the three core flows, and the open questions they carry |
| [`docs/03-domain-model.md`](docs/03-domain-model.md) | Entities, state machines, forbidden transitions, and the ten invariants — including which entities deliberately do not exist |
| [`docs/04-tasks.md`](docs/04-tasks.md) | 25 implementation tasks in dependency order, each with the spec identifiers it implements and an observable done-when |
| [`CLAUDE.md`](CLAUDE.md) | Constitution, the spec-driven loop, the traceability gate, and what counts as evidence |

Start with section 3 of the specification. It is the part the rest follows from.

## Two things worth noting

**Money is integer VND throughout.** No floating point anywhere in a money
path, and the rounding residue rule is stated rather than left to whichever
line of code runs last. This comes from building
[migration-verify](https://github.com/mohoatu/migration-verify), where the
finding was that the one-đồng differences nobody can explain are where ledgers
and migrations actually go wrong.

**Reconciliation tolerance is zero.** Not "small". A tolerance is a place for a
defect to live.

## Status

Specification, acceptance criteria, domain model and task breakdown written.

Implementation is at **tasks T01–T08**: the traceability gate, the test runner,
the money layer (integer VND arithmetic, schedule generation, payment
application, pro-rata distribution) and the append-only double-entry ledger
with zero-tolerance reconciliation. **308 checks, all passing.**

```bash
python tests/run.py              # everything
python tests/run.py --evidence   # the same, and regenerate evidence/
```

The traceability gate reports 25 of 75 documented requirements covered. That
number is meant to be read as a progress bar, which is why the gate was built
first rather than last. See [`evidence/`](evidence/).

## Open questions

Recorded rather than guessed — see section 4 of the user stories. Two of the
five are legal questions: the per-borrower exposure cap, and whether late
interest is capped by law. Neither is answered here.
