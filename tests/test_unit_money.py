"""Unit tests — money arithmetic. Task T03.

Covers spec section 5 and CLAUDE.md constitution 4.
"""

from decimal import Decimal

from harness import Suite
from src.domain.money import (
    accrue_interest,
    allocate,
    ensure_vnd,
    format_vnd,
    round_half_up,
)


def run():
    s = Suite("unit: money")

    # --- the type guard: refuse, do not convert -------------------------------
    s.equal("R6", "an int passes through unchanged", ensure_vnd(1_000), 1_000)
    s.equal("R6", "zero is a valid amount", ensure_vnd(0), 0)
    s.equal("R6", "a negative amount is valid (ledger entries have direction)", ensure_vnd(-5), -5)

    s.raises("R6", "a float is refused, not rounded", TypeError, ensure_vnd, 1000.0)
    s.raises("R6", "a float with a fraction is refused", TypeError, ensure_vnd, 1000.5)
    s.raises("R6", "a Decimal is refused", TypeError, ensure_vnd, Decimal("1000"))
    s.raises("R6", "a numeric string is refused", TypeError, ensure_vnd, "1000")
    s.raises("R6", "None is refused", TypeError, ensure_vnd, None)
    # bool is a subclass of int; True would otherwise pass as one dong.
    s.raises("R6", "True is refused despite being an int subclass", TypeError, ensure_vnd, True)
    s.raises("R6", "False is refused for the same reason", TypeError, ensure_vnd, False)

    # --- half-up rounding, both directions -----------------------------------
    s.equal("R6", "exactly half rounds up", round_half_up(5, 10), 1)
    s.equal("R6", "just under half rounds down", round_half_up(4, 10), 0)
    s.equal("R6", "just over half rounds up", round_half_up(6, 10), 1)
    s.equal("R6", "1.5 rounds to 2", round_half_up(15, 10), 2)
    s.equal("R6", "2.5 rounds to 3, not to 2 (not banker's rounding)", round_half_up(25, 10), 3)
    s.equal("R6", "3.5 rounds to 4", round_half_up(35, 10), 4)
    s.equal("R6", "an exact division is untouched", round_half_up(100, 10), 10)

    # Half-up means away from zero, as Java BigDecimal HALF_UP does. A system
    # that rounds -0.5 to 0 and 0.5 to 1 is not symmetric, and ledger entries
    # carry both signs.
    s.equal("R6", "minus a half rounds away from zero", round_half_up(-5, 10), -1)
    s.equal("R6", "minus 2.5 rounds to minus 3", round_half_up(-25, 10), -3)
    s.equal("R6", "minus just under half rounds toward zero", round_half_up(-4, 10), 0)

    s.raises("R6", "a zero denominator is refused", ValueError, round_half_up, 1, 0)
    s.raises("R6", "a negative denominator is refused", ValueError, round_half_up, 1, -10)

    # --- allocation: the final part absorbs the residue ----------------------
    s.equal("I6", "an even split is even", allocate(300, 3), (100, 100, 100))
    s.equal("I6", "the residue lands on the last part", allocate(100, 3), (33, 33, 34))
    s.equal("I6", "a residue of two also lands last", allocate(101, 3), (33, 33, 35))
    s.equal("I6", "one part takes everything", allocate(7, 1), (7,))

    for total, parts in ((100, 3), (1_000_000, 7), (12_345_679, 18), (5_000_000, 24)):
        allocation = allocate(total, parts)
        s.equal(
            "I6",
            "allocate(%d, %d) sums exactly to the total" % (total, parts),
            sum(allocation),
            total,
        )
        s.equal(
            "I6",
            "allocate(%d, %d) returns the requested number of parts" % (total, parts),
            len(allocation),
            parts,
        )

    s.raises("I6", "zero parts is refused", ValueError, allocate, 100, 0)
    s.raises("I6", "a negative number of parts is refused", ValueError, allocate, 100, -1)

    # --- accrual -------------------------------------------------------------
    # 10,000,000 at 12.00% for 365 days is 1,200,000 exactly.
    s.equal(
        "I6",
        "a full year at 12% on ten million is 1,200,000",
        accrue_interest(10_000_000, 1_200, 365),
        1_200_000,
    )
    s.equal("I6", "zero days accrues nothing", accrue_interest(10_000_000, 1_200, 0), 0)
    s.equal("I6", "a zero rate accrues nothing", accrue_interest(10_000_000, 0, 31), 0)
    s.equal("I6", "a zero balance accrues nothing", accrue_interest(0, 1_200, 31), 0)
    s.raises("I6", "a negative rate is refused", ValueError, accrue_interest, 1_000, -1, 30)
    s.raises("I6", "a negative number of days is refused", ValueError, accrue_interest, 1_000, 1_200, -1)
    s.raises("I6", "a float balance is refused", TypeError, accrue_interest, 1_000.0, 1_200, 30)

    # --- display -------------------------------------------------------------
    s.equal("A4.2", "thousands are grouped with a dot", format_vnd(12_345_678), "12.345.678")
    s.equal("A4.2", "a short amount is unchanged", format_vnd(500), "500")
    s.equal("A4.2", "zero formats as zero", format_vnd(0), "0")
    s.equal("A4.2", "a negative amount keeps its sign", format_vnd(-1_500), "-1.500")

    return s
