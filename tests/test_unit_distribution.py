"""Unit tests — pro-rata distribution. Task T06.

Covers C2.1, C2.2, C2.3, I5.
"""

import random
from datetime import date

from harness import Suite
from src.domain.distribution import Share, distribute

#: Fixed and recorded, per the task's done-when. A randomised test with an
#: unrecorded seed is not reproducible, and a failure nobody can reproduce gets
#: dismissed as a flake.
SEED = 20261123


def run():
    s = Suite("unit: distribution")

    day = date(2026, 3, 1)
    later = date(2026, 3, 2)

    # --- the adversarial case named in the task ------------------------------
    # Three equal lenders, an amount not divisible by three.
    thirds = [
        Share("L1", 1_000_000, day),
        Share("L2", 1_000_000, later),
        Share("L3", 1_000_000, date(2026, 3, 3)),
    ]
    result = distribute(100, thirds)
    s.equal("I5 C2.2", "three equal lenders, 100 dong: the parts sum to 100", sum(a.amount for a in result), 100)
    s.equal("C2.2", "the residue goes to the earliest commitment on a tie", result[0].amount, 34)
    s.equal("C2.2", "the later lenders take the floor", (result[1].amount, result[2].amount), (33, 33))

    # Two left over, so the two earliest commitments each gain one.
    result = distribute(101, thirds)
    s.equal("I5", "three equal lenders, 101 dong: the parts sum to 101", sum(a.amount for a in result), 101)
    s.equal("C2.2", "the two earliest each take a dong", (result[0].amount, result[1].amount), (34, 34))
    s.equal("C2.2", "the latest takes the floor", result[2].amount, 33)

    # --- proportionality ------------------------------------------------------
    uneven = [
        Share("A", 7_000_000, day),
        Share("B", 2_000_000, day),
        Share("C", 1_000_000, day),
    ]
    result = distribute(1_000_000, uneven)
    s.equal("C2.1", "a 70% share receives 700,000", result[0].amount, 700_000)
    s.equal("C2.1", "a 20% share receives 200,000", result[1].amount, 200_000)
    s.equal("C2.1", "a 10% share receives 100,000", result[2].amount, 100_000)
    s.equal("I5", "an exact split sums to the amount", sum(a.amount for a in result), 1_000_000)

    # --- a single lender gets everything --------------------------------------
    alone = distribute(999_983, [Share("solo", 5_000_000, day)])
    s.equal("I5", "a sole lender receives the whole amount", alone[0].amount, 999_983)

    # --- the allocation order matches the input order, not the priority order -
    # Callers index allocations against their own share list, so a reordered
    # return value would silently pay the wrong lender.
    ordered = distribute(100, thirds)
    s.equal(
        "C2.2",
        "allocations come back in the order the shares were given",
        tuple(a.lender_id for a in ordered),
        ("L1", "L2", "L3"),
    )

    # --- determinism: identical inputs, identical output ----------------------
    s.equal("C2.2", "the same inputs distribute identically", distribute(100, thirds), distribute(100, thirds))

    # Two lenders committed in the same instant: the identifier breaks the tie,
    # so the result does not depend on iteration order.
    simultaneous = [Share("zz", 1_000_000, day), Share("aa", 1_000_000, day)]
    tie = distribute(101, simultaneous)
    s.equal("I5", "a simultaneous tie still sums exactly", sum(a.amount for a in tie), 101)
    s.equal("C2.2", "the lower identifier takes the extra dong", tie[1].amount, 51)

    # --- property check over many random splits ------------------------------
    rng = random.Random(SEED)
    exact = 0
    for _ in range(2_000):
        count = rng.randint(2, 9)
        shares = [
            Share("L%02d" % k, rng.randint(500_000, 50_000_000), date(2026, 3, 1 + rng.randint(0, 20)))
            for k in range(count)
        ]
        amount = rng.randint(1, 20_000_000)
        allocations = distribute(amount, shares)
        if sum(a.amount for a in allocations) == amount:
            exact += 1
        if any(a.amount < 0 for a in allocations):
            exact = -1
            break
    s.equal("I5 C2.3", "2,000 random splits all sum exactly to the amount (seed %d)" % SEED, exact, 2_000)

    # --- input guards --------------------------------------------------------
    s.raises("I5", "a zero amount is refused", ValueError, distribute, 0, thirds)
    s.raises("I5", "a negative amount is refused", ValueError, distribute, -1, thirds)
    s.raises("I5", "a float amount is refused", TypeError, distribute, 100.0, thirds)
    s.raises("I5", "an empty share list is refused", ValueError, distribute, 100, [])
    s.raises(
        "I5",
        "a zero commitment is refused — it would be a lender with no stake",
        ValueError,
        distribute,
        100,
        [Share("X", 0, day)],
    )
    s.raises(
        "I5",
        "a float commitment is refused",
        TypeError,
        distribute,
        100,
        [Share("X", 1_000_000.0, day)],
    )

    return s
