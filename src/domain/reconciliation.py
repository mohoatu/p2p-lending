"""Daily reconciliation — derived balances against stored ones.

Implements: R6, I2, C4.1, C4.2, C4.3.
Task: T08.

**There is no tolerance parameter in this module, and that is the design.**
Not a parameter defaulting to zero, not a constant that could be edited: no
way to express "close enough". A tolerance is a place for a defect to live,
and the one place it would certainly live is a ledger that is one dong out
every day for a year before anybody asks why.

A break names the account, both figures, and the last entry posted to that
account — which is what someone investigating actually needs, rather than a
count of discrepancies.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Break:
    account_id: str
    expected: int  # derived from the ledger — the authority
    actual: int  # what the stored balance says
    last_entry_id: object

    @property
    def difference(self):
        return self.actual - self.expected

    def describe(self):
        return "%s: ledger says %d, stored says %d (out by %d), last entry %s" % (
            self.account_id,
            self.expected,
            self.actual,
            self.difference,
            self.last_entry_id,
        )


@dataclass(frozen=True)
class ChainBreak:
    account_id: str

    def describe(self):
        return "%s: the entry chain is broken or out of sequence" % self.account_id


@dataclass(frozen=True)
class ReconciliationReport:
    as_of: object
    accounts_checked: int
    entries_checked: int
    ledger_total: int
    breaks: tuple
    chain_breaks: tuple

    @property
    def passed(self):
        """True only with nothing wrong anywhere. No partial credit."""
        return not self.breaks and not self.chain_breaks and self.ledger_total == 0

    @property
    def break_count(self):
        return len(self.breaks) + len(self.chain_breaks) + (1 if self.ledger_total else 0)


def reconcile(ledger, stored_balances, as_of):
    """Compare every account's derived balance to its stored balance.

    `stored_balances` maps account_id -> integer. An account missing from it
    is treated as stored zero, because "we have no record of this account"
    and "we think it holds nothing" are the same claim as far as the money is
    concerned, and both are wrong if the ledger disagrees.
    """
    breaks = []
    chain_breaks = []

    for account_id in ledger.account_ids():
        expected = ledger.balance(account_id)
        actual = stored_balances.get(account_id, 0)
        if actual != expected:
            breaks.append(
                Break(
                    account_id=account_id,
                    expected=expected,
                    actual=actual,
                    last_entry_id=ledger.last_entry_id(account_id),
                )
            )
        if not ledger.chain_is_unbroken(account_id):
            chain_breaks.append(ChainBreak(account_id))

    # An account the store knows about and the ledger does not is also a break.
    for account_id in sorted(set(stored_balances) - set(ledger.account_ids())):
        breaks.append(
            Break(
                account_id=account_id,
                expected=0,
                actual=stored_balances[account_id],
                last_entry_id=None,
            )
        )

    return ReconciliationReport(
        as_of=as_of,
        accounts_checked=len(ledger.account_ids()),
        entries_checked=len(ledger.entries()),
        ledger_total=ledger.total(),
        breaks=tuple(breaks),
        chain_breaks=tuple(chain_breaks),
    )


def report_markdown(report, ledger, title="Reconciliation"):
    """Render a report for `evidence/reconciliation.md`."""
    lines = [
        "# %s" % title,
        "",
        "As of **%s**. %d accounts, %d ledger entries."
        % (report.as_of, report.accounts_checked, report.entries_checked),
        "",
        "Tolerance is **zero dong**. There is no parameter in `reconcile()` that",
        "could make it anything else.",
        "",
        "| Account | Purpose | Ledger balance | Entries |",
        "|---|---|---:|---:|",
    ]
    for account_id in ledger.account_ids():
        account = ledger.account(account_id)
        lines.append(
            "| `%s` | %s | %s | %d |"
            % (
                account_id,
                account.purpose + (" (external)" if account.external else ""),
                "{:,}".format(ledger.balance(account_id)).replace(",", "."),
                len(ledger.entries_for(account_id)),
            )
        )
    lines += [
        "",
        "| Check | Result |",
        "|---|---|",
        "| Balance breaks | %s |" % (len(report.breaks) or "none"),
        "| Entry-chain breaks | %s |" % (len(report.chain_breaks) or "none"),
        "| Double-entry total across all accounts | %d |" % report.ledger_total,
        "| **Verdict** | **%s** |" % ("PASSED" if report.passed else "FAILED"),
        "",
    ]
    if report.breaks or report.chain_breaks:
        lines.append("## Breaks")
        lines.append("")
        for item in list(report.breaks) + list(report.chain_breaks):
            lines.append("- %s" % item.describe())
        lines.append("")
    else:
        lines.append(
            "The double-entry total is zero, which is the arithmetic statement that"
        )
        lines.append(
            "no money was created or destroyed anywhere in this run — every dong that"
        )
        lines.append("entered an account left another one.")
        lines.append("")
    return "\n".join(lines)
