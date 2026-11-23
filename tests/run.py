"""Run every suite. The only command that matters before a commit.

Task: T02 (runner), T25 (evidence, provisional until the integration suites
exist).

    python tests/run.py              # everything
    python tests/run.py --evidence   # the same, and regenerate evidence/
    python tests/run.py --verbose    # list every check, not just the failures

Exit code is 0 only if every check passed. The traceability gate is
report-only until T24; it prints the gap and does not fail the run, because
until the implementation is complete the gap is the plan, not a defect.
"""

import importlib
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from harness import ROOT, configure_stdout, ensure_src_importable  # noqa: E402

SUITES = (
    "test_unit_money",
    "test_unit_schedule",
    "test_unit_payment",
    "test_unit_distribution",
    "test_unit_ledger",
    "test_negative_ledger",
    "test_integration_ledger",
)

TRACEABILITY_ENFORCING = False  # flipped by T24


def run_suites():
    suites = []
    for name in SUITES:
        module = importlib.import_module(name)
        suites.append(module.run())
    return suites


def print_report(suites, verbose=False, stream=sys.stdout):
    total = failed = 0
    print("p2p-lending — test run", file=stream)
    print("=" * 64, file=stream)
    for suite in suites:
        total += suite.total
        failed += len(suite.failed)
        print(
            "%-28s %4d checks  %4d passed  %4d failed"
            % (suite.name, suite.total, suite.passed, len(suite.failed)),
            file=stream,
        )
        if verbose:
            for result in suite.results:
                print(
                    "    %s  [%-12s] %s" % ("ok  " if result.ok else "FAIL", result.ids, result.description),
                    file=stream,
                )
        else:
            for result in suite.failed:
                print("    FAIL [%s] %s" % (result.ids, result.description), file=stream)
                if result.detail:
                    print("         %s" % result.detail, file=stream)
    print("-" * 64, file=stream)
    print("%d checks, %d passed, %d failed" % (total, total - failed, failed), file=stream)
    return total, failed


def write_evidence(suites, total, failed, gate_ok, gate_data):
    import traceability

    evidence = ROOT / "evidence"
    evidence.mkdir(exist_ok=True)
    (evidence / "screenshots").mkdir(exist_ok=True)

    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%SZ")
    header = [
        "Generated %s by `python tests/run.py --evidence`." % stamp,
        "Python %s on %s." % (platform.python_version(), platform.platform()),
        "",
    ]

    lines = ["# Test results", ""] + header
    lines += [
        "Every check carries the specification identifiers it proves, so this file",
        "answers \"what was proven?\" rather than only \"did it pass?\".",
        "",
        "| Suite | Checks | Passed | Failed |",
        "|---|---:|---:|---:|",
    ]
    for suite in suites:
        lines.append(
            "| %s | %d | %d | %d |" % (suite.name, suite.total, suite.passed, len(suite.failed))
        )
    lines.append("| **total** | **%d** | **%d** | **%d** |" % (total, total - failed, failed))
    lines.append("")
    for suite in suites:
        lines.append("## %s" % suite.name)
        lines.append("")
        lines.append("| Result | Ids | Check |")
        lines.append("|---|---|---|")
        for result in suite.results:
            lines.append(
                "| %s | `%s` | %s |"
                % ("pass" if result.ok else "**FAIL**", result.ids, result.description.replace("|", "\\|"))
            )
        lines.append("")
    (evidence / "results.md").write_text("\n".join(lines), encoding="utf-8")

    matrix = traceability.matrix_markdown()
    gap = [
        "",
        "## Gap",
        "",
        "Mode: **%s**." % ("enforcing" if TRACEABILITY_ENFORCING else "report-only"),
        "",
        "- documented requirements: %d" % len(gate_data["covered"] + gate_data["uncovered"]),
        "- covered by a test: %d" % len(gate_data["covered"]),
        "- uncovered: %d" % len(gate_data["uncovered"]),
        "- claimed but undocumented: %d" % len(gate_data["stale"]),
        "",
        "An uncovered requirement is a task not yet done, named. See",
        "`docs/04-tasks.md` for the order they are being closed in.",
        "",
    ]
    (evidence / "traceability.md").write_text(
        matrix + "\n".join(header) + "\n".join(gap), encoding="utf-8"
    )

    try:
        import test_integration_ledger

        body = test_integration_ledger.reconciliation_markdown()
        parts = body.split("\n", 1)
        reconciliation = parts[0] + "\n\n" + "\n".join(header) + parts[1]
    except Exception as exc:  # noqa: BLE001
        reconciliation = "\n".join(
            ["# Reconciliation", ""]
            + header
            + ["Not generated: %s" % exc, ""]
        )
    (evidence / "reconciliation.md").write_text(reconciliation, encoding="utf-8")

    with (evidence / "run.txt").open("w", encoding="utf-8") as handle:
        handle.write("\n".join(header) + "\n")
        print_report(suites, verbose=True, stream=handle)
        handle.write("\n")
        traceability.report(enforcing=TRACEABILITY_ENFORCING, stream=handle)

    # A missing picture must never be able to fail a test suite, so this is
    # best-effort and says so rather than raising.
    try:
        import capture

        capture.render()
    except Exception as exc:  # noqa: BLE001
        print("screenshot skipped: %s" % exc, file=sys.stderr)

    return evidence


def main(argv):
    configure_stdout()
    ensure_src_importable()
    verbose = "--verbose" in argv
    evidence_wanted = "--evidence" in argv

    suites = run_suites()
    total, failed = print_report(suites, verbose=verbose)

    print("", file=sys.stdout)
    import traceability

    gate_ok, gate_data = traceability.report(enforcing=TRACEABILITY_ENFORCING)

    if evidence_wanted:
        path = write_evidence(suites, total, failed, gate_ok, gate_data)
        print("", file=sys.stdout)
        print("evidence written to %s" % path, file=sys.stdout)

    return 0 if (failed == 0 and gate_ok) else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
