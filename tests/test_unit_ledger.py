"""Unit tests — the ledger. Task T07.

Covers R6, I9.
"""

from datetime import date

from harness import Suite
from src.domain.ledger import IN, OUT, Account, Ledger, Leg


def fresh():
    ledger = Ledger()
    ledger.open_account(Account("world", "external", "outside the platform", external=True))
    ledger.open_account(Account("escrow:L1", "L1", "lender escrow at partner bank"))
    ledger.open_account(Account("escrow:L2", "L2", "lender escrow at partner bank"))
    ledger.open_account(Account("escrow:BR-1", "BR-1", "borrower disbursement account"))
    return ledger


def deposit(ledger, account_id, amount, when, ref):
    return ledger.post(
        ref,
        [Leg("world", OUT, amount), Leg(account_id, IN, amount)],
        when,
    )


def run():
    s = Suite("unit: ledger")
    day = date(2026, 4, 1)

    ledger = fresh()
    s.equal("R6", "a new ledger has nothing in it", len(ledger.entries()), 0)
    s.equal("R6", "every opened account starts at zero", ledger.balance("escrow:L1"), 0)
    s.equal("R6", "the double-entry total of an empty ledger is zero", ledger.total(), 0)

    # --- posting -------------------------------------------------------------
    created = deposit(ledger, "escrow:L1", 5_000_000, day, "dep-1")
    s.equal("R6", "a two-leg posting creates two entries", len(created), 2)
    s.equal("R6", "the receiving account holds the money", ledger.balance("escrow:L1"), 5_000_000)
    s.equal("R6", "the external account is negative by the same amount", ledger.balance("world"), -5_000_000)
    s.equal("I2", "the total across all accounts is still zero", ledger.total(), 0)

    deposit(ledger, "escrow:L2", 3_000_000, day, "dep-2")
    ledger.post(
        "fund-1",
        [Leg("escrow:L1", OUT, 2_000_000), Leg("escrow:L2", OUT, 1_000_000), Leg("escrow:BR-1", IN, 3_000_000)],
        day,
        refs=("listing:LST-1",),
    )
    s.equal("R6", "a three-leg transaction moves from two accounts to one", ledger.balance("escrow:BR-1"), 3_000_000)
    s.equal("R6", "the first lender's escrow fell by its leg", ledger.balance("escrow:L1"), 3_000_000)
    s.equal("R6", "the second lender's escrow fell by its leg", ledger.balance("escrow:L2"), 2_000_000)
    s.equal("I2", "the total is still zero after a multi-leg transaction", ledger.total(), 0)

    # --- the chain (I9) ------------------------------------------------------
    chain = ledger.entries_for("escrow:L1")
    s.equal("I9", "the lender's account has two entries", len(chain), 2)
    s.equal("I9", "the first entry has no predecessor", chain[0].prev_entry_id, None)
    s.equal("I9", "the second entry points at the first", chain[1].prev_entry_id, chain[0].entry_id)
    s.equal("I9", "sequence numbers run 1..n within the account", [e.sequence for e in chain], [1, 2])
    for account_id in ledger.account_ids():
        s.check("I9", "the chain is unbroken for %s" % account_id, ledger.chain_is_unbroken(account_id))

    s.equal(
        "R6",
        "entries carry the references they were posted with",
        ledger.entries_for("escrow:BR-1")[0].refs,
        ("listing:LST-1",),
    )
    s.equal(
        "R6",
        "a transaction can be retrieved by its reference",
        len(ledger.entries_for_transaction("fund-1")),
        3,
    )

    # --- a correction is a new posting, not an edit --------------------------
    # The money went to the wrong borrower account; it is moved back by posting
    # the reverse, and both facts remain visible. This is R6 in practice.
    before = len(ledger.entries())
    ledger.post(
        "fund-1-reversal",
        [Leg("escrow:BR-1", OUT, 3_000_000), Leg("escrow:L1", IN, 2_000_000), Leg("escrow:L2", IN, 1_000_000)],
        day,
        refs=("corrects:fund-1",),
    )
    s.equal("R6", "a correction adds entries rather than removing any", len(ledger.entries()), before + 3)
    s.equal("R6", "the original posting is still in the ledger", len(ledger.entries_for_transaction("fund-1")), 3)
    s.equal("R6", "the reversal restored the first lender", ledger.balance("escrow:L1"), 5_000_000)
    s.equal("R6", "the reversal emptied the borrower account", ledger.balance("escrow:BR-1"), 0)
    s.equal("I2", "the total is zero after the correction", ledger.total(), 0)

    # --- reading does not leak the internals ---------------------------------
    s.check("R6", "entries() returns a tuple, not the internal list", isinstance(ledger.entries(), tuple))
    s.check("R6", "entries_for() returns a tuple", isinstance(ledger.entries_for("escrow:L1"), tuple))
    snapshot = len(ledger.entries())
    taken = ledger.entries()
    s.equal("R6", "a caller cannot grow the ledger through a returned value", len(taken), snapshot)

    # --- balances scale ------------------------------------------------------
    busy = fresh()
    for n in range(1, 201):
        deposit(busy, "escrow:L1", 1_000, day, "dep-%d" % n)
    s.equal("R6", "two hundred postings accumulate correctly", busy.balance("escrow:L1"), 200_000)
    s.check("I9", "the chain is unbroken across two hundred entries", busy.chain_is_unbroken("escrow:L1"))
    s.equal("I2", "the total is still zero across two hundred entries", busy.total(), 0)

    return s
