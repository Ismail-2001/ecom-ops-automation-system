#!/usr/bin/env python
"""Emit GitHub Actions ::error annotations from a pytest junitxml report.

Used by CI steps so failing test names/messages are visible through the
check-runs API and the run page even when raw logs require authentication.
"""

import sys
import xml.etree.ElementTree as ET
from pathlib import Path

MAX_ANNOTATIONS = 40


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: pytest_annotations.py <junitxml path>", file=sys.stderr)
        return 0
    path = Path(sys.argv[1])
    if not path.exists():
        print(f"::error title=pytest::no junitxml at {path}")
        return 0
    root = ET.parse(path).getroot()
    emitted = 0
    for tc in root.iter("testcase"):
        for kind in ("failure", "error"):
            for node in tc.iter(kind):
                if emitted >= MAX_ANNOTATIONS:
                    return 0
                msg = (node.get("message") or "").split("\n")[0][:300]
                where = f"{tc.get('classname', '')}::{tc.get('name', '')}"
                print(f"::error title=pytest {kind}::{where} — {msg}")
                emitted += 1
    if emitted == 0:
        print("::error title=pytest::step failed but no junitxml cases found")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
