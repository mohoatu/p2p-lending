"""Repayment schedule generation.

Implements: A4.3, A4.4, I6; spec section 5.
Task: T04.

**The amortisation method is a product decision, recorded here.** Principal is
repaid in equal instalments and interest accrues on the outstanding balance, so
the total payment declines over the term. This is what Vietnamese consumer
lenders commonly do ("tra goc deu, lai theo du no giam dan"), and it has the
practical virtue that the principal column is exact by construction, leaving
rounding to interest alone.

The consequence is that **there is no single "instalment amount"**. The first
one is the largest. `Schedule.nominal_instalment` exposes it for display, and
it must never be multiplied by the term to obtain a total — that is precisely
the ambiguity that produced 354 wrong records in the migration-verify
experiment, where one implementation printed the representative period and the
other printed the final one, and both had read the specification correctly.
"""

import calendar
from dataclasses import dataclass
from datetime import date

from .money import accrue_interest, allocate, ensure_vnd

TERMS_ALLOWED = (3, 6, 12, 18, 24)  # A1.3


def days_in_month(year, month):
    return calendar.monthrange(year, month)[1]


def add_months(start, months):
    """Add whole months, clamping the day to the end of the target month.

    31 January plus one month is 28 February, not 3 March. Clamping keeps the
    due day stable for every borrower whose disbursement fell late in a month,
    which is the behaviour a borrower expects and a spreadsheet does not.
    """
    index = start.month - 1 + months
    year = start.year + index // 12
    month = index % 12 + 1
    return date(year, month, min(start.day, days_in_month(year, month)))


@dataclass(frozen=True)
class Instalment:
    seq: int
    due_date: date
    principal: int
    interest: int

    @property
    def total(self):
        return self.principal + self.interest


@dataclass(frozen=True)
class Schedule:
    principal: int
    annual_rate_bps: int
    disbursed_on: date
    instalments: tuple

    @property
    def total_principal(self):
        return sum(i.principal for i in self.instalments)

    @property
    def total_interest(self):
        return sum(i.interest for i in self.instalments)

    @property
    def total_repayable(self):
        """What the borrower pays in full, over the term (A4.2)."""
        return sum(i.total for i in self.instalments)

    @property
    def nominal_instalment(self):
        """The first instalment's total — for display only.

        Not multipliable by the term. See the module docstring.
        """
        return self.instalments[0].total

    @property
    def final_instalment(self):
        return self.instalments[-1]


def generate(principal, annual_rate_bps, term_months, disbursed_on):
    """Build the full schedule. Deterministic: no clock, no randomness."""
    ensure_vnd(principal, "principal")
    ensure_vnd(annual_rate_bps, "annual_rate_bps")
    if principal <= 0:
        raise ValueError("principal must be positive, got %d" % principal)
    if annual_rate_bps < 0:
        raise ValueError("annual_rate_bps must not be negative")
    if term_months not in TERMS_ALLOWED:
        raise ValueError(
            "term must be one of %s months (A1.3), got %r"
            % (", ".join(str(t) for t in TERMS_ALLOWED), term_months)
        )
    if not isinstance(disbursed_on, date):
        raise TypeError("disbursed_on must be a date, got %s" % type(disbursed_on).__name__)

    principal_parts = allocate(principal, term_months)
    instalments = []
    outstanding = principal
    period_start = disbursed_on

    for seq in range(1, term_months + 1):
        due_date = add_months(disbursed_on, seq)
        days = (due_date - period_start).days
        interest = accrue_interest(outstanding, annual_rate_bps, days)
        part = principal_parts[seq - 1]
        instalments.append(Instalment(seq, due_date, part, interest))
        outstanding -= part
        period_start = due_date

    return Schedule(
        principal=principal,
        annual_rate_bps=annual_rate_bps,
        disbursed_on=disbursed_on,
        instalments=tuple(instalments),
    )
