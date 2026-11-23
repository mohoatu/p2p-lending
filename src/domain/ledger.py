"""The ledger — append-only, double-entry.

Implements: R6, I9; CLAUDE.md "Boundaries".
Task: T07.

Two decisions carry most of the weight here.

**Double entry.** Every posting moves money between accounts: the amounts
flowing out of a transaction must equal the amounts flowing in. Money
therefore cannot be created or destroyed by a bug, only misdirected — and
misdirection shows up as a balance in the wrong place rather than as a total
that quietly fails to add up. Money entering from outside (a lender funding
their escrow) is posted against an explicit external account, so "money came
from somewhere" is a recorded fact rather than an absence.

**Append-only in the type, not by discipline.** There is no update method, no
delete method, and entries are frozen. A correction is a new compensating
posting that references the original. This is what makes R6 enforceable in one
place: if a mutation path ever appears, the invariant is no longer being
enforced here, and the absence tests exist to notice.
"""

from dataclasses import dataclass

from .money import ensure_vnd

IN = "in"
OUT = "out"
DIRECTIONS = (IN, OUT)


class LedgerError(Exception):
    """A posting the ledger refuses. Refusal, not approximation."""


@dataclass(frozen=True)
class Account:
    account_id: str
    owner_party_id: str
    purpose: str
    #: True for the one account representing the world outside the platform.
    #: Its balance is the negative of everything held inside, which makes
    #: "how much money is in this system, and where did it come from" a
    #: question with an arithmetic answer.
    external: bool = False


@dataclass(frozen=True)
class Leg:
    account_id: str
    direction: str
    amount: int


@dataclass(frozen=True)
class LedgerEntry:
    entry_id: int
    account_id: str
    sequence: int
    direction: str
    amount: int
    occurred_at: object
    transaction_ref: str
    refs: tuple
    prev_entry_id: object

    @property
    def signed_amount(self):
        return self.amount if self.direction == IN else -self.amount


class Ledger:
    """A collection of accounts and the entries posted against them.

    Deliberately exposes no way to change an entry once posted. The read
    methods return tuples and plain integers, never the internal containers.
    """

    def __init__(self):
        self._accounts = {}
        self._entries = []
        self._by_account = {}

    # -- accounts ---------------------------------------------------------

    def open_account(self, account):
        if not isinstance(account, Account):
            raise TypeError("expected an Account, got %s" % type(account).__name__)
        if account.account_id in self._accounts:
            raise LedgerError("account %s already exists" % account.account_id)
        self._accounts[account.account_id] = account
        self._by_account[account.account_id] = []
        return account

    def account(self, account_id):
        try:
            return self._accounts[account_id]
        except KeyError:
            raise LedgerError("no such account: %s" % account_id) from None

    def account_ids(self):
        return tuple(sorted(self._accounts))

    # -- posting ----------------------------------------------------------

    def post(self, transaction_ref, legs, occurred_at, refs=()):
        """Append one balanced transaction. Returns the entries it created."""
        if not transaction_ref or not isinstance(transaction_ref, str):
            raise LedgerError("a transaction_ref is required")
        legs = tuple(legs)
        if len(legs) < 2:
            raise LedgerError(
                "a transaction needs at least two legs; money must come from somewhere"
            )

        total_in = total_out = 0
        for leg in legs:
            if not isinstance(leg, Leg):
                raise TypeError("expected a Leg, got %s" % type(leg).__name__)
            if leg.direction not in DIRECTIONS:
                raise LedgerError(
                    "direction must be %s, got %r" % (" or ".join(DIRECTIONS), leg.direction)
                )
            ensure_vnd(leg.amount, "leg amount")
            if leg.amount <= 0:
                raise LedgerError(
                    "a leg amount must be positive, got %d; direction carries the sign"
                    % leg.amount
                )
            if leg.account_id not in self._accounts:
                raise LedgerError("no such account: %s" % leg.account_id)
            if leg.direction == IN:
                total_in += leg.amount
            else:
                total_out += leg.amount

        if total_in != total_out:
            raise LedgerError(
                "unbalanced transaction %s: %d in, %d out (difference %d)"
                % (transaction_ref, total_in, total_out, total_in - total_out)
            )

        created = []
        for leg in legs:
            chain = self._by_account[leg.account_id]
            entry = LedgerEntry(
                entry_id=len(self._entries) + 1,
                account_id=leg.account_id,
                sequence=len(chain) + 1,
                direction=leg.direction,
                amount=leg.amount,
                occurred_at=occurred_at,
                transaction_ref=transaction_ref,
                refs=tuple(refs),
                prev_entry_id=chain[-1].entry_id if chain else None,
            )
            self._entries.append(entry)
            chain.append(entry)
            created.append(entry)
        return tuple(created)

    # -- reading ----------------------------------------------------------

    def entries(self):
        return tuple(self._entries)

    def entries_for(self, account_id):
        self.account(account_id)
        return tuple(self._by_account[account_id])

    def entries_for_transaction(self, transaction_ref):
        return tuple(e for e in self._entries if e.transaction_ref == transaction_ref)

    def balance(self, account_id):
        """Derived from the entries. There is no stored balance in here."""
        return sum(e.signed_amount for e in self.entries_for(account_id))

    def balances(self):
        return {account_id: self.balance(account_id) for account_id in self._accounts}

    def total(self):
        """Every balance summed. Double entry makes this zero, always."""
        return sum(e.signed_amount for e in self._entries)

    def last_entry_id(self, account_id):
        chain = self._by_account[self.account(account_id).account_id]
        return chain[-1].entry_id if chain else None

    def chain_is_unbroken(self, account_id):
        """I9 — each entry points at its predecessor, with no gap."""
        previous = None
        for position, entry in enumerate(self.entries_for(account_id), start=1):
            if entry.sequence != position or entry.prev_entry_id != previous:
                return False
            previous = entry.entry_id
        return True
