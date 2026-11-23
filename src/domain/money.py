"""Money arithmetic — integer VND only.

Implements: spec section 5; CLAUDE.md constitution 4.
Task: T03.

Every amount in this system is a whole number of Vietnamese dong. There is no
smaller unit, so there is no reason for a fractional type, and admitting one
would mean every downstream equality became approximate. `ensure_vnd` therefore
refuses float and Decimal rather than converting them: a conversion here is a
rounding decision taken in the wrong place, by whichever caller happened to
pass the wrong type.
"""

DAYS_PER_YEAR = 365
BPS = 10_000  # basis points in 100%; rates are integers, for the same reason


def ensure_vnd(value, field="amount"):
    """Return `value` if it is an integer number of dong, else raise TypeError.

    `bool` is rejected explicitly. It is a subclass of int, so `True` would
    otherwise pass as 1 dong.
    """
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(
            "%s must be integer VND, got %s (%r)" % (field, type(value).__name__, value)
        )
    return value


def round_half_up(numerator, denominator):
    """Divide and round to the nearest integer, halves away from zero.

    Implemented on integers throughout, so the result does not depend on binary
    floating-point representation. `denominator` must be positive; a negative
    one would make "away from zero" ambiguous, and no caller needs it.
    """
    ensure_vnd(numerator, "numerator")
    ensure_vnd(denominator, "denominator")
    if denominator <= 0:
        raise ValueError("denominator must be positive, got %d" % denominator)
    sign = -1 if numerator < 0 else 1
    magnitude = abs(numerator)
    quotient, remainder = divmod(magnitude, denominator)
    if remainder * 2 >= denominator:
        quotient += 1
    return sign * quotient


def allocate(total, parts):
    """Split `total` into `parts` whole amounts, the last absorbing the residue.

    This is the rule from spec section 5, in one place. The last part is the
    one that differs, which is why a report showing "the instalment amount" is
    ambiguous unless it says which instalment.
    """
    ensure_vnd(total, "total")
    if not isinstance(parts, int) or isinstance(parts, bool) or parts <= 0:
        raise ValueError("parts must be a positive integer, got %r" % (parts,))
    base = total // parts
    allocation = [base] * (parts - 1)
    allocation.append(total - base * (parts - 1))
    return tuple(allocation)


def accrue_interest(outstanding_principal, annual_rate_bps, days):
    """Interest on an outstanding balance for a number of days.

    Actual days over a 365-day year (spec section 5), computed as a single
    integer division so there is exactly one rounding step per period rather
    than one per intermediate term.
    """
    ensure_vnd(outstanding_principal, "outstanding_principal")
    ensure_vnd(annual_rate_bps, "annual_rate_bps")
    ensure_vnd(days, "days")
    if annual_rate_bps < 0:
        raise ValueError("annual_rate_bps must not be negative")
    if days < 0:
        raise ValueError("days must not be negative")
    return round_half_up(
        outstanding_principal * annual_rate_bps * days, BPS * DAYS_PER_YEAR
    )


def format_vnd(amount):
    """Group thousands with a dot, as Vietnamese convention has it."""
    ensure_vnd(amount)
    sign = "-" if amount < 0 else ""
    digits = str(abs(amount))
    groups = []
    while digits:
        groups.append(digits[-3:])
        digits = digits[:-3]
    return sign + ".".join(reversed(groups))
