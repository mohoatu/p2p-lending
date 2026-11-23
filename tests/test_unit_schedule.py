"""Unit tests — repayment schedule. Task T04.

Covers A4.3, A4.4, I6, A1.3.
"""

from datetime import date

from harness import Suite
from src.domain.schedule import TERMS_ALLOWED, add_months, generate


def run():
    s = Suite("unit: schedule")

    # --- month arithmetic ----------------------------------------------------
    s.equal("A4.3", "one month on from 15 Jan is 15 Feb", add_months(date(2026, 1, 15), 1), date(2026, 2, 15))
    s.equal(
        "A4.3",
        "31 Jan plus one month clamps to 28 Feb, not 3 Mar",
        add_months(date(2026, 1, 31), 1),
        date(2026, 2, 28),
    )
    s.equal(
        "A4.3",
        "31 Jan 2028 plus one month clamps to 29 Feb in a leap year",
        add_months(date(2028, 1, 31), 1),
        date(2028, 2, 29),
    )
    s.equal("A4.3", "twelve months on crosses the year", add_months(date(2026, 3, 10), 12), date(2027, 3, 10))
    s.equal("A4.3", "two months from December lands in February", add_months(date(2026, 12, 31), 2), date(2027, 2, 28))

    # --- the term is a closed set, not free text (A1.3) ----------------------
    for term in TERMS_ALLOWED:
        schedule = generate(12_000_000, 1_800, term, date(2026, 1, 15))
        s.equal("A1.3", "a %d-month term is accepted" % term, len(schedule.instalments), term)
    s.raises("A1.3", "a 7-month term is refused", ValueError, generate, 12_000_000, 1_800, 7, date(2026, 1, 15))
    s.raises("A1.3", "a zero term is refused", ValueError, generate, 12_000_000, 1_800, 0, date(2026, 1, 15))
    s.raises("A1.3", "a free-text term is refused", ValueError, generate, 12_000_000, 1_800, "6", date(2026, 1, 15))

    # --- input guards --------------------------------------------------------
    s.raises("A4.1", "a float principal is refused", TypeError, generate, 12_000_000.0, 1_800, 6, date(2026, 1, 15))
    s.raises("A4.1", "a zero principal is refused", ValueError, generate, 0, 1_800, 6, date(2026, 1, 15))
    s.raises("A4.1", "a negative rate is refused", ValueError, generate, 12_000_000, -1, 6, date(2026, 1, 15))
    s.raises("A4.1", "a string date is refused", TypeError, generate, 12_000_000, 1_800, 6, "2026-01-15")

    # --- I6: the sums must be exact, with nothing excused --------------------
    # Principals and terms chosen so that several do not divide evenly.
    cases = [
        (5_000_000, 1_500, 3),
        (7_000_000, 1_800, 6),
        (10_000_000, 1_200, 12),
        (12_345_679, 2_400, 18),
        (99_999_997, 2_050, 24),
        (100_000_000, 1_000, 24),
        (5_000_001, 3_300, 3),
    ]
    for principal, rate, term in cases:
        sch = generate(principal, rate, term, date(2026, 1, 31))
        label = "%d VND / %d bps / %dm" % (principal, rate, term)

        s.equal("I6 A4.4", "%s: principal columns sum to the principal" % label, sch.total_principal, principal)
        s.equal(
            "I6 A4.4",
            "%s: instalment totals sum to total repayable" % label,
            sum(i.total for i in sch.instalments),
            sch.total_repayable,
        )
        s.equal(
            "I6 A4.4",
            "%s: total repayable is principal plus total interest" % label,
            sch.total_repayable,
            principal + sch.total_interest,
        )
        s.check(
            "A4.3",
            "%s: every instalment has a non-negative interest figure" % label,
            all(i.interest >= 0 for i in sch.instalments),
        )
        s.check(
            "A4.3",
            "%s: due dates are strictly increasing" % label,
            all(
                sch.instalments[k].due_date < sch.instalments[k + 1].due_date
                for k in range(len(sch.instalments) - 1)
            ),
        )
        s.check(
            "A4.3",
            "%s: sequence numbers run 1..n without a gap" % label,
            [i.seq for i in sch.instalments] == list(range(1, term + 1)),
        )

    # --- the residue genuinely lands on the final instalment -----------------
    sch = generate(10_000_000, 1_200, 3, date(2026, 1, 15))
    s.equal("A4.4", "a principal not divisible by the term leaves a residue", 10_000_000 % 3, 1)
    s.equal(
        "A4.4",
        "the final instalment carries the extra dong",
        sch.final_instalment.principal - sch.instalments[0].principal,
        1,
    )

    # --- the nominal instalment is not multipliable ---------------------------
    # This is the migration-verify lesson as an assertion: a single displayed
    # "instalment amount" times the term is NOT the total, and any report that
    # implies otherwise is wrong. Declining balance makes the first the largest.
    sch = generate(12_000_000, 2_400, 12, date(2026, 1, 15))
    s.check(
        "A4.4",
        "nominal instalment times the term overstates the total",
        sch.nominal_instalment * 12 > sch.total_repayable,
    )
    s.check(
        "A4.2",
        "the final period's interest is far below the first's",
        sch.final_instalment.interest < sch.instalments[0].interest // 4,
    )

    # Interest is NOT monotonically decreasing, and that surprise is pinned
    # here on purpose. Accrual uses actual days (spec section 5), so the
    # 28-day February period costs less than the 31-day March period that
    # follows it, even though principal fell in between. A reviewer comparing
    # this schedule against one built on a 30-day month convention would see a
    # difference in every row and no error anywhere — which is the whole
    # argument of migration-verify, arriving here as a property of the product.
    rises = [
        k
        for k in range(len(sch.instalments) - 1)
        if sch.instalments[k + 1].interest > sch.instalments[k].interest
    ]
    s.equal(
        "A4.2",
        "interest rises exactly once, after the short February period",
        rises,
        [1],
    )
    s.equal(
        "A4.2",
        "the rise is from the February period to the March one",
        (sch.instalments[1].due_date.month, sch.instalments[2].due_date.month),
        (3, 4),
    )

    # --- determinism ---------------------------------------------------------
    first = generate(7_777_777, 1_950, 18, date(2026, 2, 28))
    second = generate(7_777_777, 1_950, 18, date(2026, 2, 28))
    s.equal("A4.3", "the same inputs produce an identical schedule", first, second)

    # --- a zero rate is a valid loan, and must not divide by zero ------------
    free = generate(6_000_000, 0, 6, date(2026, 1, 15))
    s.equal("I6", "an interest-free loan repays exactly the principal", free.total_repayable, 6_000_000)
    s.equal("I6", "an interest-free loan accrues no interest", free.total_interest, 0)

    return s
