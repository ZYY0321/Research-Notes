import argparse
import html
from truncator.common.capture_files import capture_image
from pathlib import Path
from truncator.common.storage import read, save
from truncator.source.project import scan, prepare
from truncator.mutation.mutations import plans
from truncator.execution.build import build
from truncator.execution.device.runtime import capture
from truncator.execution.workflow import batch, review, status
from truncator.review.datasets.dataset import export_dataset
from truncator.mutation.operators import UX_OPERATORS
from truncator.review.review_policy import RECOVERY_STATUSES
from truncator.source.binding import bind_candidates
from truncator.source.configuration import profile_from_source, load_campaign
from truncator.execution.campaign import campaign
from truncator.planning.calibration import plan_for_target


def create_parser():
    parser = argparse.ArgumentParser(description="ArkUI truncation mutation workbench")
    parser.add_argument("--profile")
    commands = parser.add_subparsers(dest="command", required=True)
    sub = commands.add_parser("run-summary")
    sub.add_argument("--runs", nargs="+", required=True)
    sub.add_argument("--out", required=True)
    sub = commands.add_parser("dataset-audit")
    sub.add_argument("--exports", nargs="+", required=True)
    sub.add_argument("--targets")
    sub.add_argument("--revisions", choices=["latest", "all"], default="latest",
                     help="Count latest reviewed rebuilds, or retain all historical versions")
    sub.add_argument("--candidates", help="Directory of remaining plan JSON files")
    sub.add_argument("--out", required=True)
    sub = commands.add_parser("record-review")
    sub.add_argument("--run", required=True)
    sub.add_argument("--review", required=True)
    sub = commands.add_parser("curate")
    sub.add_argument("--run", required=True)
    sub.add_argument("--review", required=True)
    sub.add_argument("--out", required=True)
    sub.add_argument("--device", required=True)
    sub = commands.add_parser("instrument")
    sub.add_argument("--out", required=True)
    sub = commands.add_parser("report")
    sub.add_argument("--runs", required=True)
    sub = commands.add_parser("init-profile")
    sub.add_argument("--source", required=True)
    sub.add_argument("--studio", required=True)
    sub.add_argument("--module")
    sub.add_argument("--out", required=True)
    sub = commands.add_parser("campaign")
    sub.add_argument("--spec", required=True)
    sub.add_argument("--runs", required=True)
    sub.add_argument("--device", required=True)
    sub = commands.add_parser("scan")
    sub.add_argument("--out", required=True)
    sub = commands.add_parser("plan")
    sub.add_argument("--catalog", required=True)
    sub.add_argument("--out", required=True)
    sub.add_argument("--seed", type=int, default=1)
    sub.add_argument("--count", type=int, default=1)
    sub.add_argument("--operator", choices=UX_OPERATORS, required=True)
    sub.add_argument("--width", type=float, default=80)
    sub.add_argument("--height", type=float, default=12)
    sub.add_argument("--widths", help="Comma-separated width parameter domain")
    sub.add_argument("--heights", help="Comma-separated height parameter domain")
    sub.add_argument("--lines", type=int, default=1)
    sub.add_argument("--file", default="")
    sub.add_argument("--site")
    sub.add_argument("--parameters", help="JSON file with explicit operator parameters")
    sub = commands.add_parser("bind")
    sub.add_argument("--catalog", required=True)
    sub.add_argument("--capture", required=True)
    sub.add_argument("--out", required=True)
    sub.add_argument("--file", default="")
    sub = commands.add_parser("geometry-plan")
    sub.add_argument("--catalog", required=True)
    sub.add_argument("--capture", required=True)
    sub.add_argument(
        "--binding", required=True, help="JSON containing site and selector"
    )
    sub.add_argument("--operator", required=True, choices=UX_OPERATORS)
    sub.add_argument(
        "--px-per-vp", type=float, help="Override measured display density"
    )
    domain = sub.add_mutually_exclusive_group()
    domain.add_argument(
        "--penetrations",
        help="Explicit pixel candidates; omit for automatic calibration",
    )
    domain.add_argument(
        "--ratios",
        help="Explicit reproduction schedule; omit to compute one baseline-dependent plan",
    )
    sub.add_argument("--edge", choices=["top", "bottom", "left", "right"])
    sub.add_argument(
        "--budget",
        type=int,
        default=3,
        help="Limit explicit schedules; default automatic planning produces one plan",
    )
    sub.add_argument("--color")
    domain.add_argument(
        "--foreground-fraction",
        type=float,
        help="Opt-in flat-background Text content calibration, between 0 and 1",
    )
    sub.add_argument("--occluder", help="JSON binding for an existing sibling")
    sub.add_argument("--out", required=True)
    sub = commands.add_parser("prepare")
    sub.add_argument("--run", required=True)
    sub.add_argument("--plan")
    sub = commands.add_parser("build")
    sub.add_argument("--run", required=True)
    sub = commands.add_parser("capture")
    sub.add_argument("--run", required=True)
    sub.add_argument("--device", required=True)
    sub.add_argument("--recipe", required=True)
    sub.add_argument("--continue-from", help="Capture directory from the live process; skips install and relaunch")
    sub = commands.add_parser("review")
    sub.add_argument("--runs", required=True)
    sub.add_argument("--out", required=True)
    sub = commands.add_parser("batch")
    sub.add_argument("--force-capture", action="store_true")
    sub.add_argument("--plans", required=True)
    sub.add_argument("--runs", required=True)
    sub.add_argument("--device")
    sub.add_argument("--recipe")
    sub = commands.add_parser("status")
    sub.add_argument("--runs", required=True)
    sub = commands.add_parser("export")
    sub.add_argument("--runs", required=True)
    sub.add_argument("--out", required=True)
    sub = commands.add_parser("annotate")
    sub.add_argument("--capture", required=True)
    sub.add_argument(
        "--decision", choices=["accepted", "rejected", "needs-review"], required=True
    )
    sub.add_argument("--reviewer", required=True)
    sub.add_argument("--reason", required=True)
    sub.add_argument("--boxes")
    sub.add_argument("--content-status", choices=["clipped", "complete", "uncertain"])
    sub.add_argument("--recovery-status", choices=sorted(RECOVERY_STATUSES))
    sub.add_argument("--evidence-capture", action="append", default=[], help="Additional capture directory from the same HAP; repeat for each interaction state")
    return parser


def main():
    parser = create_parser()
    args = parser.parse_args()
    if args.command == "run-summary":
        from truncator.review.reporting.run_summary import summarize_runs
        save(args.out, summarize_runs(args.runs))
        print(args.out)
        return
    if args.command == "dataset-audit":
        from truncator.review.datasets.dataset_balance import audit_exports, rank_replenishment
        result = audit_exports(args.exports, read(args.targets) if args.targets else None, revisions=args.revisions)
        if args.candidates:
            candidates = [read(p) for p in sorted(Path(args.candidates).glob("*.json"))]
            result["replenishment"] = rank_replenishment([p for p in candidates if "operator" in p and "site" in p], result)
        save(args.out, result)
        print(args.out)
        return
    if args.command == "record-review":
        from truncator.review.review_evidence import record_review

        print(record_review(args.run, args.review))
        return
    if args.command == "curate":
        from truncator.execution.curation import rebuild_reviewed

        result = rebuild_reviewed(args.run, args.review, args.out, args.device)
        print(result)
        if result["status"] == "failed":
            raise SystemExit(1)
        return
    if args.command == "report":
        from truncator.review.reporting.evidence import generate_report

        print(generate_report(args.runs))
        return
    if args.command == "export":
        print("exported samples", export_dataset(args.runs, args.out))
        return
    if args.command == "init-profile":
        if Path(args.out).exists():
            raise FileExistsError(args.out)
        save(args.out, profile_from_source(args.source, args.studio, args.module))
        return
    if args.command == "campaign":
        result = campaign(load_campaign(args.spec), args.runs, args.device)
        for row in result:
            print(row.get("application"), row.get("status"), "targets=" + str(row.get("planned_targets", 0)))
        print("Results:", Path(args.runs).resolve() / "results.json")
        if any(r["status"] == "failed" for r in result):
            raise SystemExit(1)
        return
    if not args.profile:
        parser.error("--profile is required for this command")
    profile = read(args.profile)
    if args.command == "instrument":
        from truncator.source.instrumentation import instrument

        instrument(profile, args.out)
        print(Path(args.out).resolve() / "profile.json")
    elif args.command == "scan":
        catalog = scan(profile)
        save(args.out, catalog)
        print(
            "sites",
            len(catalog["sites"]),
            "files with parse errors",
            len(catalog["diagnostics"]),
        )
    elif args.command == "plan":
        result = plans(
            read(args.catalog),
            args.seed,
            args.count,
            args.operator,
            (
                read(args.parameters)
                if args.parameters
                else {
                    "width": (
                        [float(v) for v in args.widths.split(",")]
                        if args.widths
                        else args.width
                    ),
                    "height": (
                        [float(v) for v in args.heights.split(",")]
                        if args.heights
                        else args.height
                    ),
                    "lines": args.lines,
                }
            ),
            args.file,
            args.site,
        )
        out = Path(args.out)
        out.mkdir(parents=True, exist_ok=True)
        for plan in result:
            path = out / (plan["id"] + ".json")
            if path.exists():
                raise FileExistsError(path)
            save(path, plan)
            print(path)
    elif args.command == "bind":
        save(
            args.out,
            bind_candidates(
                read(args.catalog),
                read(Path(args.capture) / "tree-before.json"),
                args.file,
            ),
        )
    elif args.command == "geometry-plan":
        result = plan_for_target(
            read(args.catalog),
            args.capture,
            read(args.binding),
            args.operator,
            density=args.px_per_vp,
            edge=args.edge,
            budget=args.budget,
            color=args.color,
            occluder=read(args.occluder) if args.occluder else None,
            penetrations=(
                [float(value) for value in args.penetrations.split(",")]
                if args.penetrations is not None
                else None
            ),
            ratios=(
                [float(value) for value in args.ratios.split(",")]
                if args.ratios is not None
                else None
            ),
            foreground_fraction=args.foreground_fraction,
        )
        for plan in result:
            path = Path(args.out) / (plan["id"] + ".json")
            if path.exists():
                raise FileExistsError(path)
            save(path, plan)
            print(path)
    elif args.command == "prepare":
        prepare(profile, args.run, read(args.plan) if args.plan else None)
    elif args.command == "build":
        build(profile, args.run)
    elif args.command == "capture":
        print(
            capture(
                profile,
                args.run,
                args.device,
                read(args.recipe),
                Path(args.run).resolve().parent,
                continue_from=args.continue_from,
            )
        )
    elif args.command == "review":
        sections = []
        for record in sorted(Path(args.runs).rglob("capture.json")):
            screenshot = capture_image(record.parent)
            if screenshot.exists():
                label = html.escape(str(screenshot.parent))
                sections.append(
                    f'<article><h2>{label}</h2><img src="{screenshot.resolve().as_uri()}"><pre>{html.escape(record.read_text(encoding="utf-8"))}</pre></article>'
                )
        Path(args.out).write_text(
            '<!doctype html><meta charset="utf-8"><title>截断注入审核</title><style>body{font-family:sans-serif}article{display:inline-block;vertical-align:top;width:46%;margin:1%}img{width:100%}pre{white-space:pre-wrap}h2{font-size:14px}</style>'
            + "".join(sections),
            encoding="utf-8",
        )
    elif args.command == "batch":
        if args.device and not args.recipe:
            parser.error("--device requires --recipe")
        result = batch(
            profile,
            list(Path(args.plans).glob("*.json")),
            args.runs,
            args.device,
            read(args.recipe) if args.recipe else None,
            force_capture=args.force_capture,
        )
        print(result)
        if any(r["status"] == "failed" for r in result):
            raise SystemExit(1)
    elif args.command == "status":
        print(status(args.runs))
    elif args.command == "annotate":
        print(
            review(
                args.capture,
                args.decision,
                args.reviewer,
                args.reason,
                read(args.boxes) if args.boxes else [],
                content_status=args.content_status,
                recovery_status=args.recovery_status,
                evidence_captures=args.evidence_capture,
            )
        )


if __name__ == "__main__":
    main()
