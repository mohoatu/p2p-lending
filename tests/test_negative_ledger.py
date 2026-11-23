"""Negative tests — the ledger refuses. Tasks T07, T08.

Covers R6, I2, I9, C4.2, C4.3.

CLAUDE.md: "the negative suite is the product". For a ledger, what it will not
do matters more than what it will, because every way it could be persuaded to
lose a dong is a way an auditor's question becomes unanswerable.
"""

import dataclasses
import inspect
from datetime import date

from harness import Suite
from src.domain import reconciliation as recon_module
from src.domain.ledger import IN, OUT, Account, Ledger, LedgerError, Leg
from src.domain.reconciliation import reconcile

FORBIDDEN_METHOD_NAMES = (
    "update",
    "update_entry",
    "edit",
    "edit_entry",
    "delete",
    "delete_entry",
    "remove",
    "remove_entry",
    "amend",
    "void",
    "set_balance",
    "adjust_balance",
    "overwrite",
    "clear",
    "truncate",
)


def fresh():
    ledger = Ledger()
    ledger.open_account(Account("world", "external", "outside the platform", external=True))
    ledger.open_account(Account("escrow:L1", "L1", "lender escrow"))
    ledger.open_account(Account("escrow:BR-1", "BR-1", "borrower account"))
    ledger.post(
        "dep-1",
        [Leg("world", OUT, 1_000_000), Leg("escrow:L1", IN, 1_000_000)],
        date(2026, 4, 1),
    )
    return ledger


def run():
    s = Suite("negative: ledger")
    day = date(2026, 4, 1)
    ledger = fresh()
    entry = ledger.entries()[0]

    # --- a posted entry cannot be mutated (R6) -------------------------------
    def change_amount():
        entry.amount = 1

    def change_account():
        entry.account_id = "escrow:BR-1"

    def change_chain():
        entry.prev_entry_id = 999

    s.raises("R6", "the amount on a posted entry cannot be changed", dataclasses.FrozenInstanceError, change_amount)
    s.raises("R6", "the account on a posted entry cannot be changed", dataclasses.FrozenInstanceError, change_account)
    s.raises("R6", "the chain link on a posted entry cannot be rewritten", dataclasses.FrozenInstanceError, change_chain)

    # --- the ledger exposes no mutation path at all --------------------------
    present = [name for name in FORBIDDEN_METHOD_NAMES if hasattr(Ledger, name)]
    s.equal(
        "R6",
        "the Ledger class has no update, delete, amend or override method",
        present,
        [],
    )
    public = [name for name in dir(Ledger) if not name.startswith("_")]
    s.equal(
        "R6",
        "the only method that changes the ledger is post()",
        sorted(n for n in public if n in ("post", "open_account")),
        ["open_account", "post"],
    )

    # --- unbalanced money is refused, in both directions ---------------------
    s.raises(
        "I2",
        "a transaction with more going in than out is refused",
        LedgerError,
        ledger.post,
        "bad-1",
        [Leg("world", OUT, 100), Leg("escrow:L1", IN, 101)],
        day,
    )
    s.raises(
        "I2",
        "a transaction with more going out than in is refused",
        LedgerError,
        ledger.post,
        "bad-2",
        [Leg("world", OUT, 101), Leg("escrow:L1", IN, 100)],
        day,
    )
    s.raises(
        "I2",
        "a one-dong imbalance is refused, the same as a large one",
        LedgerError,
        ledger.post,
        "bad-3",
        [Leg("world", OUT, 1_000_000), Leg("escrow:L1", IN, 999_999)],
        day,
    )

    # --- money cannot appear from nowhere ------------------------------------
    s.raises(
        "I2",
        "a single-leg posting is refused — money must come from somewhere",
        LedgerError,
        ledger.post,
        "bad-4",
        [Leg("escrow:L1", IN, 100)],
        day,
    )
    s.raises("I2", "an empty posting is refused", LedgerError, ledger.post, "bad-5", [], day)

    # --- leg validation ------------------------------------------------------
    s.raises(
        "R6",
        "a zero-amount leg is refused",
        LedgerError,
        ledger.post,
        "bad-6",
        [Leg("world", OUT, 0), Leg("escrow:L1", IN, 0)],
        day,
    )
    s.raises(
        "R6",
        "a negative leg is refused — direction carries the sign, not the amount",
        LedgerError,
        ledger.post,
        "bad-7",
        [Leg("world", OUT, -100), Leg("escrow:L1", IN, -100)],
        day,
    )
    s.raises(
        "R6",
        "a float amount is refused at the ledger boundary too",
        TypeError,
        ledger.post,
        "bad-8",
        [Leg("world", OUT, 100.0), Leg("escrow:L1", IN, 100.0)],
        day,
    )
    s.raises(
        "R6",
        "an unknown direction is refused",
        LedgerError,
        ledger.post,
        "bad-9",
        [Leg("world", "sideways", 100), Leg("escrow:L1", IN, 100)],
        day,
    )
    s.raises(
        "R6",
        "posting to an account that was never opened is refused",
        LedgerError,
        ledger.post,
        "bad-10",
        [Leg("world", OUT, 100), Leg("escrow:ghost", IN, 100)],
        day,
    )
    s.raises(
        "R6",
        "a posting without a transaction reference is refused",
        LedgerError,
        ledger.post,
        "",
        [Leg("world", OUT, 100), Leg("escrow:L1", IN, 100)],
        day,
    )
    s.raises("R6", "opening the same account twice is refused", LedgerError, ledger.open_account, Account("escrow:L1", "L1", "duplicate"))
    s.raises("R6", "reading an account that does not exist is refused", LedgerError, ledger.balance, "escrow:ghost")

    # Nothing above was allowed to land.
    s.equal(
        "I2",
        "after every refused posting the ledger is unchanged",
        (len(ledger.entries()), ledger.balance("escrow:L1"), ledger.total()),
        (2, 1_000_000, 0),
    )

    # --- reconciliation has no tolerance, and cannot be given one ------------
    parameters = list(inspect.signature(reconcile).parameters)
    s.equal("C4.2", "reconcile() takes exactly ledger, stored balances and a date", parameters, ["ledger", "stored_balances", "as_of"])
    s.check(
        "C4.2",
        "no parameter of reconcile() mentions tolerance, threshold or epsilon",
        not any(word in p.lower() for p in parameters for word in ("toler", "thresh", "epsilon", "delta")),
    )
    source = inspect.getsource(recon_module)
    s.check(
        "C4.2",
        "the reconciliation module defines no tolerance constant",
        not any(word in source.lower().replace("tolerance is", "").replace("a tolerance", "") for word in ("tolerance =", "threshold =", "epsilon =")),
    )

    # --- a corrupted stored balance produces exactly one break ---------------
    stored = dict(ledger.balances())
    report = reconcile(ledger, stored, day)
    s.check("C4.1", "a clean ledger reconciles with no breaks", report.passed)
    s.equal("C4.1", "and reports zero breaks", report.break_count, 0)

    stored["escrow:L1"] = stored["escrow:L1"] + 1
    report = reconcile(ledger, stored, day)
    s.check("C4.3", "a one-dong discrepancy fails the reconciliation", not report.passed)
    s.equal("C4.3", "exactly one break is reported", len(report.breaks), 1)
    s.equal("C4.3", "the break names the account", report.breaks[0].account_id, "escrow:L1")
    s.equal("C4.3", "it reports what the ledger says", report.breaks[0].expected, 1_000_000)
    s.equal("C4.3", "it reports what the store says", report.breaks[0].actual, 1_000_001)
    s.equal("C4.3", "it reports the difference", report.breaks[0].difference, 1)
    s.equal(
        "C4.3",
        "it names the last entry posted to that account",
        report.breaks[0].last_entry_id,
        ledger.last_entry_id("escrow:L1"),
    )

    # An account the store knows about and the ledger does not.
    stored = dict(ledger.balances())
    stored["escrow:phantom"] = 50_000
    report = reconcile(ledger, stored, day)
    s.equal("C4.3", "an account unknown to the ledger is itself a break", len(report.breaks), 1)
    s.equal("C4.3", "the phantom account is named", report.breaks[0].account_id, "escrow:phantom")

    # A missing account is treated as stored zero, and so is a break.
    stored = dict(ledger.balances())
    del stored["escrow:L1"]
    report = reconcile(ledger, stored, day)
    s.equal("C4.3", "an account missing from the store is a break, not a skip", len(report.breaks), 1)
    s.equal("C4.3", "it is reported as stored zero", report.breaks[0].actual, 0)

    return s
