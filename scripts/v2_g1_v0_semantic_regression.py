from __future__ import annotations

import argparse
import json
import os
import tempfile
from pathlib import Path

from g05_semantic_equivalence import (
    _collect_semantics,
    _first_difference,
    _json_bytes,
    _materialize_commit,
    _run_collector,
)

BASE_COMMIT = "078b3cfc948262bb71604a631e17972f8ad11a1f"
EXPECTED_SEMANTIC_VECTOR_SHA256 = "4aa007b39b060a954695b0d484a28723f9eb0c1949fc98e10c9c6c7ded4c20f0"


def _driver() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    script = Path(__file__).resolve()

    with tempfile.TemporaryDirectory(prefix="arc-mkii-v2-g1-v0-") as tmp:
        tmp_root = Path(tmp)
        base_root = tmp_root / "base"
        base_root.mkdir()
        _materialize_commit(BASE_COMMIT, base_root)
        base_output = tmp_root / "base.json"
        current_output = tmp_root / "current.json"
        _run_collector(script, base_root, base_output)
        _run_collector(script, repo_root, current_output)
        base = json.loads(base_output.read_text(encoding="utf-8"))
        current = json.loads(current_output.read_text(encoding="utf-8"))

    if base != current:
        print("V2 G1 V0 SEMANTIC REGRESSION: FAIL")
        print(_first_difference(base, current) or "unknown semantic mismatch")
        return 1

    actual = current.get("semantic_vector_sha256")
    if actual != EXPECTED_SEMANTIC_VECTOR_SHA256:
        print("V2 G1 V0 SEMANTIC REGRESSION: FAIL")
        print(f"semantic vector {actual} != frozen certificate {EXPECTED_SEMANTIC_VECTOR_SHA256}")
        return 1

    print("V2 G1 V0 SEMANTIC REGRESSION: PASS")
    print(f"base={BASE_COMMIT}")
    print("frozen_menus=320 (256 TRAIN + 64 EVAL)")
    print(f"training_rows={current['training_row_count']}")
    print(f"semantic_vector_sha256={actual}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--collect", type=Path)
    args = parser.parse_args()
    if args.collect is not None:
        repo_root = Path(os.environ["ARC_MKII_G05_REPO_ROOT"])
        args.collect.write_bytes(_json_bytes(_collect_semantics(repo_root)) + b"\n")
        return 0
    return _driver()


if __name__ == "__main__":
    raise SystemExit(main())
