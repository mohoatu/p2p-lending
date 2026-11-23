"""Payment application and settlement quotes.

Implements: C1.1, C1.3, C1.4, I4; spec section 5.
Task: T05.

The order fees -> late interest -> interest -> principal is a business decision
and lives here, named, rather than being wherever the code happens to subtract
first. What arrived and how it was interpreted are kept as separate facts
(domain model decision 3): `amount_received` is what the borrower paid, and the
tuple of `Application` rows is what the platform decided it meant. Conflating
them is how a dispute becomes unanswerable.

Anything left over after every bucket is satisfied is recorded as `UNAPPLIED`
rather than dropped, so that the sum of the rows always equals the amount
received (I4). A payment that vanishes into a rounding step is the defect this
invariant exists to catch.
"""

from dataclasses import dataclass

from .money import ensure_vnd

FEES = "fees"
LATE_INTEREST = "late_interest"
INTEREST = "interest"
PRINCIPAL = "principal"
UNAPPLIED = "unapplied"

#: C1.1 — the stated order. Changing it is a product decision, not a refactor.
ORDER = (FEES, LATE_INTEREST, INTEREST, PRINCIPAL)


@dataclass(frozen=True)
class Application:
    seq: int
    bucket: str
    amount: int


def apply_payment(amount_received, due):
    """Split `amount_received` across the buckets in `ORDER`.

    `due` maps bucket -> amount owed. For PRINCIPAL, pass the whole outstanding
    principal rather than just the instalment's share: an overpayment reduces
    principal (C1.3), and that is expressed by letting the bucket be as large
    as the debt actually is.
    """
    ensure_vnd(amount_received, "amount_received")
    if amount_received <= 0:
        raise ValueError("amount_received must be positive, got %d" % amount_received)

    unknown = set(due) - set(ORDER)
    if unknown:
        raise ValueError("unknown payment buckets: %s" % ", ".join(sorted(unknown)))

    applications = []
    remaining = amount_received
    seq = 0

    for bucket in ORDER:
        owed = ensure_vnd(due.get(bucket, 0), bucket)
        if owed < 0:
            raise ValueError("%s owed must not be negative, got %d" % (bucket, owed))
        if remaining <= 0:
            break
        take = min(remaining, owed)
        if take > 0:
            seq += 1
            applications.append(Application(seq, bucket, take))
            remaining -= take

    if remaining > 0:
        seq += 1
        applications.append(Application(seq, UNAPPLIED, remaining))

    return tuple(applications)


def applied_to(applications, bucket):
    return sum(a.amount for a in applications if a.bucket == bucket)


def settlement_quote(outstanding_principal, interest_to_date, fees=0, late_interest=0):
    """What it costs to clear the loan today, and not one dong beyond (C1.4).

    `interest_to_date` is accrued up to today by the caller, which is where the
    clock lives. Interest for days that have not happened is not quoted.
    """
    ensure_vnd(outstanding_principal, "outstanding_principal")
    ensure_vnd(interest_to_date, "interest_to_date")
    ensure_vnd(fees, "fees")
    ensure_vnd(late_interest, "late_interest")
    for name, value in (
        ("outstanding_principal", outstanding_principal),
        ("interest_to_date", interest_to_date),
        ("fees", fees),
        ("late_interest", late_interest),
    ):
        if value < 0:
            raise ValueError("%s must not be negative, got %d" % (name, value))
    return outstanding_principal + interest_to_date + fees + late_interest
