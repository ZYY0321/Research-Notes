"""Explicit research commands, separate from generation and sample-quality review."""
import argparse
from truncator.common.storage import read, save
from research.production_evidence.comparison import inspect_target, compare_targets
from research.production_evidence.case_evidence import template, validate


def main():
    parser = argparse.ArgumentParser(description="Commercial case comparison and research evidence")
    commands = parser.add_subparsers(dest="command", required=True)
    sub = commands.add_parser("inspect-target")
    for name in ("tree", "screenshot", "selector", "out"):
        sub.add_argument("--" + name, required=True)
    sub = commands.add_parser("compare-targets")
    for name in ("reference", "injected", "out"):
        sub.add_argument("--" + name, required=True)
    sub = commands.add_parser("case-template")
    for name in ("capture", "out"):
        sub.add_argument("--" + name, required=True)
    sub = commands.add_parser("case-review")
    for name in ("capture", "review", "out"):
        sub.add_argument("--" + name, required=True)
    args = parser.parse_args()
    if args.command == "inspect-target":
        result = inspect_target(args.tree, args.screenshot, read(args.selector))
    elif args.command == "compare-targets":
        result = compare_targets(read(args.reference), read(args.injected))
    elif args.command == "case-template":
        result = template(args.capture)
    else:
        result = validate(read(args.review), args.capture)
    save(args.out, result)
    print(args.out)


if __name__ == "__main__":
    main()
