"""Pro-rata distribution of a repayment across lenders.

Implements: C2.1, C2.2, C2.3, I5.
Task: T06.

A received amount almost never divides cleanly by the lenders' shares, so some
dong are left over. There are only three things that can happen to them: they
can be dropped, duplicated, or allocated by a rule. The first two are defects
that reconciliation will find a day later; the third needs the rule to be
written down, which is what this module is.

**The rule: largest remainder, ties broken by earliest commitment, then by
lender identifier.** The second tiebreak exists only to make the result
deterministic when two lenders committed in the same instant — without it, the
output would depend on dictionary ordering, and a test that passes for that
reason is not evidence of anything.
"""

from dataclasses import dataclass

from .money import ensure_vnd


@dataclass(frozen=True)
class Share:
    lender_id: str
    committed: int
    committed_at: object  # a date or datetime; compared, never arithmetic


@dataclass(frozen=True)
class Allocation:
    lender_id: str
    amount: int


def distribute(amount, shares):
    """Split `amount` across `shares` in proportion to committed principal.

    Returns one Allocation per share, in the order given, whose amounts sum
    exactly to `amount` (I5, C2.2).
    """
    ensure_vnd(amount, "amount")
    if amount <= 0:
        raise ValueError("amount must be positive, got %d" % amount)
    if not shares:
        raise ValueError("no shares to distribute to")

    total_committed = 0
    for share in shares:
        ensure_vnd(share.committed, "committed")
        if share.committed <= 0:
            raise ValueError(
                "committed must be positive for %s, got %d"
                % (share.lender_id, share.committed)
            )
        total_committed += share.committed

    rows = []
    for index, share in enumerate(shares):
        quotient, remainder = divmod(amount * share.committed, total_committed)
        rows.append(
            {
                "index": index,
                "lender_id": share.lender_id,
                "amount": quotient,
                "remainder": remainder,
                "committed_at": share.committed_at,
            }
        )

    residue = amount - sum(row["amount"] for row in rows)
    if residue < 0:  # pragma: no cover - arithmetically impossible, kept as a guard
        raise AssertionError("over-allocated by %d" % -residue)

    priority = sorted(
        rows,
        key=lambda row: (-row["remainder"], row["committed_at"], row["lender_id"]),
    )
    for offset in range(residue):
        priority[offset]["amount"] += 1

    return tuple(Allocation(row["lender_id"], row["amount"]) for row in rows)
