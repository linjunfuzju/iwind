"""Audit JSONL splits for group, exact-text, and near-text contamination."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

try:
    from .audit import audit_splits, findings_as_dicts
    from .build_corpus import read_jsonl
    from .statistics import write_json
except ImportError:  # Support direct execution from this directory.
    from audit import audit_splits, findings_as_dicts
    from build_corpus import read_jsonl
    from statistics import write_json


def main(args: argparse.Namespace) -> int:
    records_by_split = {
        split: [record for _, record in read_jsonl(path)]
        for split, path in (("train", args.train), ("validation", args.validation), ("test", args.test))
        if path is not None
    }
    findings = audit_splits(records_by_split, near_threshold=args.near_threshold)
    report = {
        "clean": not findings,
        "near_threshold": args.near_threshold,
        "findings": findings_as_dicts(findings),
    }
    write_json(args.output, report)
    return 1 if findings and args.fail_on_findings else 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--train", type=Path, required=True)
    parser.add_argument("--validation", type=Path)
    parser.add_argument("--test", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--near-threshold", type=float, default=0.85)
    parser.add_argument("--fail-on-findings", action="store_true")
    raise SystemExit(main(parser.parse_args()))
