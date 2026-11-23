"""Minimal test harness. Vanilla Python, no pytest (CLAUDE.md constitution 7).

Task: T02.

Every check carries the specification identifiers it proves, because that is
what makes the traceability gate possible and what makes `evidence/` readable
by someone who has not seen the code.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def configure_stdout():
    """Make stdout UTF-8.

    The banned-vocabulary list contains Vietnamese ("bao dam von" with
    diacritics), and the Windows console is cp1252. Printing those strings
    without this raises UnicodeEncodeError and the failure looks like a test
    failure rather than a console problem — a day lost to exactly this in
    migration-verify.
    """
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):  # pragma: no cover
            pass


def ensure_src_importable():
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))


class Result:
    __slots__ = ("ids", "description", "ok", "detail")

    def __init__(self, ids, description, ok, detail=None):
        self.ids = ids
        self.description = description
        self.ok = ok
        self.detail = detail


class Suite:
    """A named group of checks."""

    def __init__(self, name):
        self.name = name
        self.results = []

    def check(self, ids, description, condition, detail=None):
        ok = bool(condition)
        self.results.append(Result(ids, description, ok, None if ok else detail))
        return ok

    def equal(self, ids, description, actual, expected):
        ok = actual == expected
        return self.check(
            ids,
            description,
            ok,
            detail=None if ok else "expected %r, got %r" % (expected, actual),
        )

    def raises(self, ids, description, exception, fn, *args, **kwargs):
        """Assert that calling `fn` refuses, rather than approximating.

        Constitution 3: refusal over approximation. Most of this product's
        value is in what it will not do, so this is the most used method here.
        """
        try:
            fn(*args, **kwargs)
        except exception:
            return self.check(ids, description, True)
        except Exception as exc:  # noqa: BLE001 - a wrong refusal is still a failure
            return self.check(
                ids,
                description,
                False,
                detail="expected %s, got %s: %s"
                % (exception.__name__, type(exc).__name__, exc),
            )
        return self.check(ids, description, False, detail="no exception raised")

    @property
    def total(self):
        return len(self.results)

    @property
    def failed(self):
        return [r for r in self.results if not r.ok]

    @property
    def passed(self):
        return self.total - len(self.failed)

    def claimed_ids(self):
        ids = set()
        for result in self.results:
            ids.update(result.ids.split())
        return ids
