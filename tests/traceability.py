"""The traceability gate — does every documented requirement have a test?

Task: T01 (report-only), T24 (enforcing).
Implements: CLAUDE.md "Traceability".

Built before the implementation on purpose. A gate added at the end can only
report on what was already written; a gate present from the start makes the gap
visible on every run, and the gap shrinking is the progress report.

It checks **both directions**:

  - a documented requirement with no test is uncovered;
  - a test claiming an identifier that no document defines is a stale claim.

The second direction is the one that catches a renamed section, and it is the
reason the gate is worth more than a coverage percentage.

Run standalone:  python tests/traceability.py
"""

import re
import sys
from pathlib import Path

from harness import ROOT, configure_stdout

DOC_SPEC = ROOT / "docs" / "01-product-spec.md"
DOC_STORIES = ROOT / "docs" / "02-user-stories.md"
DOC_MODEL = ROOT / "docs" / "03-domain-model.md"
TESTS_DIR = ROOT / "tests"

STORY_HEADING = re.compile(r"^###\s+(?P<id>[ABC]\d+)\s")
NUMBERED_ITEM = re.compile(r"^(?P<n>\d+)\.\s")
TABLE_ROW = re.compile(r"^\|\s*(?P<id>[IR]\d+)\s*\|(?P<rest>.*)$")
SECTION_HEADING = re.compile(r"^##\s")

SINGULAR = {"rules": "rule", "invariants": "invariant", "criteria": "criterion"}

#: A string literal made up only of identifiers is how a test claims coverage.
CLAIM_LITERAL = re.compile(
    r"""["'](?P<ids>[ABCIR]\d+(?:\.\d+)?(?:\s+[ABCIR]\d+(?:\.\d+)?)*)["']"""
)


def read(path):
    return path.read_text(encoding="utf-8").splitlines()


def parse_acceptance_criteria(path=DOC_STORIES):
    """Derive A1.1 .. Cn.m from the numbered lists under each story heading."""
    criteria = []
    current = None
    highest = 0
    for line in read(path):
        heading = STORY_HEADING.match(line)
        if heading:
            if current:
                criteria.extend("%s.%d" % (current, n) for n in range(1, highest + 1))
            current = heading.group("id")
            highest = 0
            continue
        if current and SECTION_HEADING.match(line):
            criteria.extend("%s.%d" % (current, n) for n in range(1, highest + 1))
            current = None
            highest = 0
            continue
        if current:
            item = NUMBERED_ITEM.match(line)
            if item:
                highest = max(highest, int(item.group("n")))
    if current:
        criteria.extend("%s.%d" % (current, n) for n in range(1, highest + 1))
    return criteria


def parse_table_ids(path, prefix):
    """Collect I* or R* identifiers from a markdown table.

    A row whose last cell is an em dash declares itself unprovable by test —
    R7 (the two-year sandbox limit) is a roadmap fact, not a system rule — and
    is excluded rather than carried forever as an uncovered requirement.
    """
    found = []
    for line in read(path):
        row = TABLE_ROW.match(line)
        if not row or not row.group("id").startswith(prefix):
            continue
        cells = [c.strip() for c in row.group("rest").split("|")]
        cells = [c for c in cells if c != ""]
        if cells and cells[-1] in ("-", "—", "--"):
            continue
        found.append(row.group("id"))
    return found


def documented_ids():
    return {
        "criteria": parse_acceptance_criteria(),
        "invariants": parse_table_ids(DOC_MODEL, "I"),
        "rules": parse_table_ids(DOC_SPEC, "R"),
    }


def claimed_ids(tests_dir=TESTS_DIR):
    """Identifiers claimed by test files, found statically.

    Static rather than by importing and running, so the gate can be read as a
    standalone answer to "what does this suite say it proves?".
    """
    claims = {}
    for path in sorted(tests_dir.glob("test_*.py")):
        text = path.read_text(encoding="utf-8")
        for match in CLAIM_LITERAL.finditer(text):
            for identifier in match.group("ids").split():
                claims.setdefault(identifier, set()).add(path.name)
    return claims


def report(enforcing=False, stream=sys.stdout):
    documented = documented_ids()
    every = []
    for kind in ("rules", "invariants", "criteria"):
        every.extend((kind, i) for i in documented[kind])

    claims = claimed_ids()
    known = {i for _, i in every}

    covered = [(k, i) for k, i in every if i in claims]
    uncovered = [(k, i) for k, i in every if i not in claims]
    stale = sorted(i for i in claims if i not in known)

    print("Traceability gate %s" % ("(enforcing)" if enforcing else "(report-only)"), file=stream)
    print("-" * 64, file=stream)
    print(
        "documented requirements : %d  (%d rules, %d invariants, %d criteria)"
        % (
            len(every),
            len(documented["rules"]),
            len(documented["invariants"]),
            len(documented["criteria"]),
        ),
        file=stream,
    )
    print("covered by a test       : %d" % len(covered), file=stream)
    print("uncovered               : %d" % len(uncovered), file=stream)
    print("claimed but undocumented: %d" % len(stale), file=stream)

    if uncovered:
        print("", file=stream)
        print("Uncovered — this is the backlog in a second form:", file=stream)
        for kind, identifier in uncovered:
            print("  %-10s %s" % (SINGULAR[kind], identifier), file=stream)

    if stale:
        print("", file=stream)
        print("Claimed but not defined in any document — a rename went unfixed:", file=stream)
        for identifier in stale:
            print("  %s  (claimed by %s)" % (identifier, ", ".join(sorted(claims[identifier]))), file=stream)

    ok = not stale and (not uncovered or not enforcing)
    return ok, {
        "documented": documented,
        "claims": claims,
        "covered": covered,
        "uncovered": uncovered,
        "stale": stale,
    }


def matrix_markdown():
    """The spec-to-test matrix for evidence/traceability.md."""
    documented = documented_ids()
    claims = claimed_ids()
    lines = [
        "# Traceability matrix",
        "",
        "Generated by `tests/traceability.py`. Each documented requirement and the",
        "test files that claim to prove it. An empty cell is an uncovered",
        "requirement, not an oversight that went unnoticed.",
        "",
        "| Kind | Id | Proven by |",
        "|---|---|---|",
    ]
    for kind, key in (("rule", "rules"), ("invariant", "invariants"), ("criterion", "criteria")):
        for identifier in documented[key]:
            files = ", ".join(sorted(claims.get(identifier, ()))) or "—"
            lines.append("| %s | %s | %s |" % (kind, identifier, files))
    lines.append("")
    return "\n".join(lines)


if __name__ == "__main__":
    configure_stdout()
    enforcing = "--enforcing" in sys.argv
    ok, _ = report(enforcing=enforcing)
    sys.exit(0 if ok else 1)
