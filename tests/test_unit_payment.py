"""Unit tests — payment application and settlement. Task T05.

Covers C1.1, C1.3, C1.4, I4.
"""

from harness import Suite
from src.domain.money import accrue_interest
from src.domain.payment import (
    FEES,
    INTEREST,
    LATE_INTEREST,
    ORDER,
    PRINCIPAL,
    UNAPPLIED,
    apply_payment,
    applied_to,
    settlement_quote,
)


def run():
    s = Suite("unit: payment")

    # --- the order is the business decision, so assert the order itself ------
    s.equal(
        "C1.1",
        "the application order is fees, late interest, interest, principal",
        ORDER,
        (FEES, LATE_INTEREST, INTEREST, PRINCIPAL),
    )

    due = {FEES: 50_000, LATE_INTEREST: 30_000, INTEREST: 200_000, PRINCIPAL: 1_000_000}

    # A payment that covers everything.
    full = apply_payment(1_280_000, due)
    s.equal("C1.1", "a full payment produces one row per bucket", len(full), 4)
    s.equal("C1.1", "fees are satisfied first", full[0].bucket, FEES)
    s.equal("C1.1", "late interest is satisfied second", full[1].bucket, LATE_INTEREST)
    s.equal("C1.1", "interest is satisfied third", full[2].bucket, INTEREST)
    s.equal("C1.1", "principal is satisfied last", full[3].bucket, PRINCIPAL)
    s.equal("I4", "a full payment sums to the amount received", sum(a.amount for a in full), 1_280_000)

    # A payment smaller than the fee — the hardest case to get right, because
    # it must not touch any later bucket at all.
    tiny = apply_payment(10_000, due)
    s.equal("C1.1", "a payment under the fee produces exactly one row", len(tiny), 1)
    s.equal("C1.1", "that row is the fee", tiny[0].bucket, FEES)
    s.equal("I4", "it sums to the amount received", sum(a.amount for a in tiny), 10_000)
    s.equal("C1.1", "no principal is touched", applied_to(tiny, PRINCIPAL), 0)
    s.equal("C1.1", "no interest is touched", applied_to(tiny, INTEREST), 0)

    # A payment that stops part-way through a bucket.
    partial = apply_payment(100_000, due)
    s.equal("C1.1", "the fee is fully satisfied", applied_to(partial, FEES), 50_000)
    s.equal("C1.1", "late interest is fully satisfied", applied_to(partial, LATE_INTEREST), 30_000)
    s.equal("C1.1", "interest takes only what is left", applied_to(partial, INTEREST), 20_000)
    s.equal("C1.1", "principal is untouched", applied_to(partial, PRINCIPAL), 0)
    s.equal("I4", "a partial payment sums to the amount received", sum(a.amount for a in partial), 100_000)

    # --- overpayment reduces principal, and nothing is dropped (C1.3, I4) ----
    over = apply_payment(2_000_000, due)
    s.equal("C1.3", "principal absorbs up to the whole outstanding balance", applied_to(over, PRINCIPAL), 1_000_000)
    s.equal("C1.3", "what remains after the debt is recorded as unapplied", applied_to(over, UNAPPLIED), 720_000)
    s.equal("I4", "an overpayment still sums to the amount received", sum(a.amount for a in over), 2_000_000)
    s.check(
        "I4",
        "an overpayment loses nothing — no row is silently dropped",
        applied_to(over, FEES)
        + applied_to(over, LATE_INTEREST)
        + applied_to(over, INTEREST)
        + applied_to(over, PRINCIPAL)
        + applied_to(over, UNAPPLIED)
        == 2_000_000,
    )

    # A payment against a settled loan: nothing is due, everything is unapplied.
    nothing_due = apply_payment(500_000, {})
    s.equal("I4", "with nothing owed the whole payment is unapplied", applied_to(nothing_due, UNAPPLIED), 500_000)
    s.equal("I4", "and it still sums to the amount received", sum(a.amount for a in nothing_due), 500_000)

    # --- exactness across a spread of awkward amounts ------------------------
    for amount in (1, 7, 49_999, 50_000, 50_001, 279_999, 280_000, 280_001, 1_279_999, 1_280_001, 9_999_999):
        rows = apply_payment(amount, due)
        s.equal("I4", "%d dong: the rows sum to the amount received" % amount, sum(a.amount for a in rows), amount)
        s.check(
            "I4",
            "%d dong: every row is a positive amount" % amount,
            all(a.amount > 0 for a in rows),
        )
        s.check(
            "C1.1",
            "%d dong: rows are numbered 1..n in order" % amount,
            [a.seq for a in rows] == list(range(1, len(rows) + 1)),
        )

    # --- input guards --------------------------------------------------------
    s.raises("I4", "a zero payment is refused", ValueError, apply_payment, 0, due)
    s.raises("I4", "a negative payment is refused", ValueError, apply_payment, -1, due)
    s.raises("I4", "a float payment is refused", TypeError, apply_payment, 100_000.0, due)
    s.raises("I4", "an unknown bucket is refused", ValueError, apply_payment, 100_000, {"penalty": 1})
    s.raises("I4", "a negative amount owed is refused", ValueError, apply_payment, 100_000, {FEES: -1})
    s.raises("I4", "a float amount owed is refused", TypeError, apply_payment, 100_000, {FEES: 1.0})

    # --- settlement quotes today, and not one dong beyond (C1.4) -------------
    # 10,000,000 at 18% for 45 days.
    interest_to_date = accrue_interest(10_000_000, 1_800, 45)
    quote = settlement_quote(10_000_000, interest_to_date)
    s.equal("C1.4", "a settlement quote is principal plus interest to date", quote, 10_000_000 + interest_to_date)
    s.check(
        "C1.4",
        "the quote is strictly less than one with a day of future interest",
        quote < settlement_quote(10_000_000, accrue_interest(10_000_000, 1_800, 46)),
    )
    s.equal(
        "C1.4",
        "fees and late interest are included when present",
        settlement_quote(1_000_000, 10_000, fees=5_000, late_interest=2_000),
        1_017_000,
    )
    s.equal("C1.4", "a settled loan quotes zero", settlement_quote(0, 0), 0)
    s.raises("C1.4", "a negative principal is refused", ValueError, settlement_quote, -1, 0)
    s.raises("C1.4", "a float in a quote is refused", TypeError, settlement_quote, 1_000_000.0, 0)

    # Paying the quote exactly clears the loan with nothing left over.
    cleared = apply_payment(quote, {INTEREST: interest_to_date, PRINCIPAL: 10_000_000})
    s.equal("C1.4", "paying the quote leaves nothing unapplied", applied_to(cleared, UNAPPLIED), 0)
    s.equal("C1.4", "paying the quote clears the principal", applied_to(cleared, PRINCIPAL), 10_000_000)

    return s
