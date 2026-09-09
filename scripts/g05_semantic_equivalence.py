from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path
from types import SimpleNamespace

BASE_COMMIT = "c9897ae02829aeed31cccdaef662de4c715b312e"
HARDENING_SOURCE_COMMIT = "f794a157213636c4a9e52540e667a3892d6a2e26"
SCHEMA = "arc-reactor-mkii-g05-semantic-equivalence/v0"


def _json_bytes(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _fraction(value) -> list[int]:
    return [value.numerator, value.denominator]


def _record_digest(records) -> tuple[int, str]:
    digest = hashlib.sha256()
    count = 0
    for record in records:
        digest.update(_json_bytes(record))
        digest.update(b"\n")
        count += 1
    return count, digest.hexdigest()


def _load_frozen_menus(repo_root: Path):
    from arc_mkii.canonical import canonical_id
    from arc_mkii.domain import Menu

    def load(name: str):
        menus = []
        path = repo_root / "experiments" / "v0" / "protocol" / name
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line:
                continue
            record = json.loads(line)
            menu = Menu(tuple(record["queries"]))
            if canonical_id(menu) != record["canonical_id"]:
                raise AssertionError(f"canonical identity mismatch in {path}")
            menus.append(menu)
        return menus

    return load("TRAIN_MENUS.jsonl"), load("EVAL_MENUS.jsonl")


def _decision_record(decision) -> dict[str, object]:
    return {
        "candidate_mask": decision.candidate_mask,
        "remaining_budget": decision.remaining_budget,
        "scores": [[query_id, _fraction(score)] for query_id, score in decision.scores],
        "chosen_query": decision.chosen_query,
    }


def _case_record(case) -> dict[str, object]:
    return {
        "canonical_task_id": case.canonical_task_id,
        "budget": case.budget,
        "fault": case.fault,
        "selected_query_ids": list(case.selected_query_ids),
        "observed_bits": list(case.observed_bits),
        "candidate_masks_after_queries": list(case.candidate_masks_after_queries),
        "decisions": [_decision_record(decision) for decision in case.decisions],
        "repair": case.repair,
        "success": case.success,
        "query_count": case.query_count,
    }


def _collect_semantics(repo_root: Path) -> dict[str, object]:
    from arc_mkii.canonical import canonical_id
    from arc_mkii.corpus import build_training_rows
    from arc_mkii.evaluate import evaluate_theta, ignition_pass
    from arc_mkii.fit import fit_theta
    from arc_mkii.scramble import scramble_feedback
    from arc_mkii.selector import THETA0

    train_menus, eval_menus = _load_frozen_menus(repo_root)
    all_menus = train_menus + eval_menus

    membership = {
        "train": [
            {"canonical_id": canonical_id(menu), "queries": list(menu.queries)}
            for menu in train_menus
        ],
        "eval": [
            {"canonical_id": canonical_id(menu), "queries": list(menu.queries)}
            for menu in eval_menus
        ],
    }

    rows = build_training_rows(train_menus)
    scrambled_rows = scramble_feedback(rows)
    learn_theta = fit_theta(rows)
    scrambled_theta = fit_theta(scrambled_rows)
    frozen_theta = tuple(THETA0)
    thetas = {
        "LEARN": learn_theta,
        "SCRAMBLED": scrambled_theta,
        "FROZEN": frozen_theta,
    }

    scramble_count, scramble_digest = _record_digest(
        {"row_id": row.row_id, "feedback": scrambled.feedback}
        for row, scrambled in sorted(
            zip(rows, scrambled_rows),
            key=lambda pair: pair[0].row_id,
        )
    )

    eval_ids = {canonical_id(menu) for menu in eval_menus}
    behavior: dict[str, object] = {}
    eval_success: dict[str, dict[int, int]] = {}
    for arm, theta in thetas.items():
        result = evaluate_theta(arm, theta, all_menus)
        case_count, case_digest = _record_digest(
            _case_record(case) for case in result.case_traces
        )
        behavior[arm] = {
            "case_count": case_count,
            "case_sha256": case_digest,
            "success_all_by_budget": {
                str(budget): result.success_by_budget[budget] for budget in (2, 3)
            },
        }
        per_budget = {2: 0, 3: 0}
        for case in result.case_traces:
            if case.canonical_task_id in eval_ids:
                per_budget[case.budget] += case.success
        eval_success[arm] = per_budget

    ignition = ignition_pass(
        SimpleNamespace(success_by_budget=eval_success["LEARN"]),
        SimpleNamespace(success_by_budget=eval_success["SCRAMBLED"]),
        SimpleNamespace(success_by_budget=eval_success["FROZEN"]),
        transplant_ok=True,
    )

    record: dict[str, object] = {
        "schema": SCHEMA,
        "frozen_menu_membership": membership,
        "training_row_count": len(rows),
        "theta": {
            arm: [_fraction(value) for value in theta]
            for arm, theta in thetas.items()
        },
        "scramble_assignment": {
            "count": scramble_count,
            "sha256": scramble_digest,
        },
        "behavior_all_320_menus": behavior,
        "eval_success_by_budget": {
            arm: {str(budget): values[budget] for budget in (2, 3)}
            for arm, values in eval_success.items()
        },
        "ignition_pass": ignition,
    }
    record["semantic_vector_sha256"] = hashlib.sha256(_json_bytes(record)).hexdigest()
    return record


def _run_collector(script: Path, repo_root: Path, output: Path) -> None:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(repo_root / "src")
    env["ARC_MKII_G05_REPO_ROOT"] = str(repo_root)
    env["PYTHONNOUSERSITE"] = "1"
    subprocess.run(
        [sys.executable, str(script), "--collect", str(output)],
        check=True,
        cwd=repo_root,
        env=env,
    )


def _materialize_commit(commit: str, destination: Path) -> None:
    archive = subprocess.check_output(["git", "archive", "--format=tar", commit])
    with tarfile.open(fileobj=io.BytesIO(archive), mode="r:") as tar:
        tar.extractall(destination, filter="data")


def _assert_hardening_source_is_frozen(repo_root: Path) -> None:
    subprocess.run(
        [
            "git",
            "diff",
            "--exit-code",
            HARDENING_SOURCE_COMMIT,
            "--",
            "src/arc_mkii",
            "experiments/v0/protocol",
        ],
        cwd=repo_root,
        check=True,
    )


def _first_difference(left: object, right: object, path: str = "$") -> str | None:
    if type(left) is not type(right):
        return f"{path}: type {type(left).__name__} != {type(right).__name__}"
    if isinstance(left, dict):
        if set(left) != set(right):
            return f"{path}: keys {sorted(left)} != {sorted(right)}"
        for key in sorted(left):
            found = _first_difference(left[key], right[key], f"{path}.{key}")
            if found:
                return found
        return None
    if isinstance(left, list):
        if len(left) != len(right):
            return f"{path}: length {len(left)} != {len(right)}"
        for index, (a, b) in enumerate(zip(left, right)):
            found = _first_difference(a, b, f"{path}[{index}]")
            if found:
                return found
        return None
    if left != right:
        return f"{path}: {left!r} != {right!r}"
    return None


def _driver() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    script = Path(__file__).resolve()
    _assert_hardening_source_is_frozen(repo_root)

    with tempfile.TemporaryDirectory(prefix="arc-mkii-g05-") as tmp:
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
        print("G0.5 SEMANTIC EQUIVALENCE: FAIL")
        print(_first_difference(base, current) or "unknown semantic mismatch")
        return 1

    print("G0.5 SEMANTIC EQUIVALENCE: PASS")
    print(f"base={BASE_COMMIT}")
    print(f"hardened_source={HARDENING_SOURCE_COMMIT}")
    print("frozen_menus=320 (256 TRAIN + 64 EVAL)")
    print(f"training_rows={current['training_row_count']}")
    print(f"semantic_vector_sha256={current['semantic_vector_sha256']}")
    print(
        "eval_success="
        + json.dumps(current["eval_success_by_budget"], sort_keys=True, separators=(",", ":"))
    )
    print(f"ignition_pass={str(current['ignition_pass']).lower()}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--collect", type=Path)
    args = parser.parse_args()
    if args.collect is not None:
        repo_root = Path(os.environ["ARC_MKII_G05_REPO_ROOT"])
        record = _collect_semantics(repo_root)
        args.collect.write_bytes(_json_bytes(record) + b"\n")
        return 0
    return _driver()


if __name__ == "__main__":
    raise SystemExit(main())
