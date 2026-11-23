"""Integration — money layer and ledger together, over a whole loan.

Tasks: T07, T08 (a first integration run; the full lifecycle is T23).
Covers I2, I3, I5, C2.4, C4.1, B3.5, B4.5.

Two lenders fund one loan, the borrower repays every instalment, each
repayment is distributed pro rata, and the ledger is reconciled at the end.
Nothing is asserted from the output: the expected figures come from the
specification — instalments sum to total repayable, distributions sum to each
repayment, and the double-entry total is zero.
"""

from datetime import date

from harness import Suite
from src.domain.distribution import Share, distribute
from src.domain.ledger import IN, OUT, Account, Ledger, Leg
from src.domain.payment import INTEREST, PRINCIPAL, apply_payment
from src.domain.reconciliation import reconcile, report_markdown
from src.domain.schedule import generate

PRINCIPAL_VND = 10_000_000
RATE_BPS = 1_800  # 18.00% a year
TERM = 6
DISBURSED_ON = date(2026, 4, 1)

COMMITMENTS = (
    ("L1", 7_000_000, date(2026, 3, 20)),
    ("L2", 3_000_000, date(2026, 3, 21)),
)


def build():
    """Run the scenario. Returns (ledger, schedule, distributions, facts)."""
    ledger = Ledger()
    ledger.open_account(Account("world", "external", "outside the platform", external=True))
    ledger.open_account(Account("platform:fees", "platform", "the platform's own fee income"))
    for lender_id, _, _ in COMMITMENTS:
        ledger.open_account(Account("escrow:%s" % lender_id, lender_id, "lender escrow at partner bank"))
    ledger.open_account(Account("escrow:BR-1", "BR-1", "borrower account at partner bank"))

    # 1. Lenders fund their escrow from outside.
    for lender_id, amount, when in COMMITMENTS:
        ledger.post(
            "deposit:%s" % lender_id,
            [Leg("world", OUT, amount), Leg("escrow:%s" % lender_id, IN, amount)],
            when,
        )

    # 2. The listing fills and is disbursed. Note that no leg touches
    #    platform:fees — lender principal never passes through the platform.
    ledger.post(
        "disbursement:LN-1",
        [Leg("escrow:%s" % lid, OUT, amount) for lid, amount, _ in COMMITMENTS]
        + [Leg("escrow:BR-1", IN, PRINCIPAL_VND)],
        DISBURSED_ON,
        refs=("loan:LN-1",),
    )

    # 2b. The borrower spends the principal on whatever they borrowed it for.
    #     Without this the loan proceeds would sit in escrow and the account
    #     would look settled at the end for the wrong reason.
    ledger.post(
        "drawdown:LN-1",
        [Leg("escrow:BR-1", OUT, PRINCIPAL_VND), Leg("world", IN, PRINCIPAL_VND)],
        DISBURSED_ON,
        refs=("loan:LN-1",),
    )

    schedule = generate(PRINCIPAL_VND, RATE_BPS, TERM, DISBURSED_ON)
    shares = [Share(lid, amount, when) for lid, amount, when in COMMITMENTS]

    # 3. Each instalment: the borrower funds their account from outside, pays,
    #    and the payment is distributed pro rata.
    distributions = []
    outstanding = PRINCIPAL_VND
    for instalment in schedule.instalments:
        due = instalment.total
        ledger.post(
            "income:BR-1:%d" % instalment.seq,
            [Leg("world", OUT, due), Leg("escrow:BR-1", IN, due)],
            instalment.due_date,
        )
        applications = apply_payment(
            due, {INTEREST: instalment.interest, PRINCIPAL: outstanding}
        )
        allocations = distribute(due, shares)
        ledger.post(
            "repayment:LN-1:%d" % instalment.seq,
            [Leg("escrow:BR-1", OUT, due)]
            + [Leg("escrow:%s" % a.lender_id, IN, a.amount) for a in allocations],
            instalment.due_date,
            refs=("loan:LN-1", "instalment:%d" % instalment.seq),
        )
        distributions.append((instalment, applications, allocations))
        outstanding -= instalment.principal

    facts = {
        "total_repayable": schedule.total_repayable,
        "final_outstanding": outstanding,
    }
    return ledger, schedule, distributions, facts


def run():
    s = Suite("integration: ledger")
    ledger, schedule, distributions, facts = build()

    # --- the loan was funded by the commitments, exactly (I3) ---------------
    s.equal(
        "I3 B3.5",
        "the commitments sum to the principal",
        sum(amount for _, amount, _ in COMMITMENTS),
        PRINCIPAL_VND,
    )
    s.equal(
        "B4.5",
        "the borrower received exactly the principal at disbursement",
        sum(e.amount for e in ledger.entries_for_transaction("disbursement:LN-1") if e.direction == IN),
        PRINCIPAL_VND,
    )
    s.equal(
        "R1",
        "no lender principal passed through a platform account",
        ledger.balance("platform:fees"),
        0,
    )
    s.equal(
        "R1",
        "the platform's account has no entries at all in this run",
        len(ledger.entries_for("platform:fees")),
        0,
    )

    # --- every repayment was distributed in full (I5, C2.4) -----------------
    for instalment, applications, allocations in distributions:
        label = "instalment %d" % instalment.seq
        s.equal(
            "I4",
            "%s: the payment application sums to the amount paid" % label,
            sum(a.amount for a in applications),
            instalment.total,
        )
        s.equal(
            "I5 C2.4",
            "%s: the distribution sums to the amount paid" % label,
            sum(a.amount for a in allocations),
            instalment.total,
        )
        s.equal(
            "C2.4",
            "%s: one ledger entry per lender, plus the borrower's leg" % label,
            len(ledger.entries_for_transaction("repayment:LN-1:%d" % instalment.seq)),
            len(COMMITMENTS) + 1,
        )

    # --- the loan is fully repaid -------------------------------------------
    s.equal("I6", "every dong of principal was scheduled", facts["final_outstanding"], 0)
    total_to_lenders = sum(
        ledger.balance("escrow:%s" % lid) for lid, _, _ in COMMITMENTS
    )
    s.equal(
        "I5",
        "the lenders hold exactly the total repayable at the end",
        total_to_lenders,
        facts["total_repayable"],
    )
    s.equal(
        "C4.1",
        "the borrower's account is empty once the loan is repaid",
        ledger.balance("escrow:BR-1"),
        0,
    )

    # Each lender's return is proportional, and the parts still sum exactly.
    for lender_id, committed, _ in COMMITMENTS:
        received = ledger.balance("escrow:%s" % lender_id)
        s.check(
            "C2.1",
            "%s received more than they committed" % lender_id,
            received > committed,
        )
    s.equal(
        "I5",
        "the lenders' returns sum to the total repaid, with nothing lost to rounding",
        total_to_lenders,
        sum(i.total for i in schedule.instalments),
    )

    # --- reconciliation at the close of the run (C4.1, I2, I9) --------------
    report = reconcile(ledger, ledger.balances(), date(2026, 10, 1))
    s.check("C4.1", "the run reconciles with no breaks", report.passed)
    s.equal("C4.1", "no balance breaks", len(report.breaks), 0)
    s.equal("I9", "no entry-chain breaks", len(report.chain_breaks), 0)
    s.equal("I2", "the double-entry total across every account is zero", report.ledger_total, 0)
    s.equal(
        "I2",
        "the external account holds the negative of everything inside",
        ledger.balance("world"),
        -sum(
            ledger.balance(a) for a in ledger.account_ids() if a != "world"
        ),
    )

    # --- determinism ---------------------------------------------------------
    again, _, _, _ = build()
    s.equal(
        "C4.1",
        "running the scenario twice produces identical balances",
        again.balances(),
        ledger.balances(),
    )

    return s


def reconciliation_markdown():
    """The report written to evidence/reconciliation.md."""
    ledger, _, _, _ = build()
    report = reconcile(ledger, ledger.balances(), date(2026, 10, 1))
    body = report_markdown(
        report, ledger, title="Reconciliation — integration run (ledger scenario)"
    )
    return body + "\n".join(
        [
            "",
            "## What this run was",
            "",
            "Two lenders fund one %s VND loan at %.2f%% over %d months; the borrower"
            % ("{:,}".format(PRINCIPAL_VND).replace(",", "."), RATE_BPS / 100, TERM),
            "repays every instalment; each repayment is distributed pro rata. Scope is",
            "the money layer and the ledger (tasks T03-T08). The application, listing",
            "and loan state machines are not in it yet, so this is not the full",
            "lifecycle run of task T23 and does not claim to be.",
            "",
        ]
    )
