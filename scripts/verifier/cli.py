"""Command-line entry point: argument parsing, rendering, and exit codes."""

import argparse
import json
from pathlib import Path

from .core import Verifier
from .model import Status

DESCRIPTION = "Check repository conventions and invoke Claude's native validator."
DEFAULT_ROOT = Path(__file__).resolve().parents[2]


def exit_code(status: Status) -> int:
    match status:
        case Status.PASS:
            return 0
        case Status.FAILED:
            return 1
        case Status.INCONCLUSIVE:
            return 2


def render_text(report: dict) -> None:
    for item in report["checks"]:
        print(f"{item['status']}: {item['check']}: {item['detail']}")
    print(f"{report['status']}: overall")


def parse_args(argv=None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=DESCRIPTION)
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--skip-native", action="store_true")
    return parser.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)
    verifier = Verifier(args.root)
    verifier.structure()
    verifier.native(args.skip_native)
    report = verifier.report()
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        render_text(report)
    return exit_code(report["status"])
