from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import time
import tracemalloc
from dataclasses import asdict
from pathlib import Path
from typing import Sequence

from .artifact import load_artifact, save_artifact
from .canonical import canonical_id
from .corpus import build_training_rows
from .domain import Menu
from .fit import fit_theta
from .evaluate import evaluate_theta, ignition_pass, transplant_equivalent
from .planner import planner_reference
from .manifests import generate_protocol_menus, protocol_record
from .protocol import verify_protocol
from .resources import ResourceCounter
from .scramble import (
    scramble_descriptor,
    scramble_descriptor_from_menus,
    scramble_feedback,
)
from .selector import THETA0


def _json_bytes(record: object) -> bytes:
    return (json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def _jsonl_bytes(records: Sequence[object]) -> bytes:
    return b"".join(_json_bytes(record) for record in records)


def _menu_record(menu) -> dict[str, object]:
    return {"canonical_id": canonical_id(menu), "queries": list(menu.queries)}


def freeze_protocol(out: str | Path) -> None:
    out = Path(out)
    train_menus, eval_menus = generate_protocol_menus()

    cheap_payloads: dict[str, bytes] = {
        "PROTOCOL.json": _json_bytes(protocol_record()),
        "TRAIN_MENUS.jsonl": _jsonl_bytes([_menu_record(menu) for menu in train_menus]),
        "EVAL_MENUS.jsonl": _jsonl_bytes([_menu_record(menu) for menu in eval_menus]),
    }

    if out.exists():
        expected_names = set(cheap_payloads) | {"SCRAMBLE.json", "MANIFEST_SHA256.txt"}
        if {path.name for path in out.iterdir()} != expected_names:
            raise FileExistsError("existing protocol directory has unexpected or missing files")
        for name, content in cheap_payloads.items():
            if (out / name).read_bytes() != content:
                raise FileExistsError(
                    f"existing protocol directory is not byte-identical: {out / name}"
                )
        manifest_lines = (out / "MANIFEST_SHA256.txt").read_text(encoding="ascii").splitlines()
        recorded: dict[str, str] = {}
        for line in manifest_lines:
            digest, name = line.split("  ", 1)
            recorded[name] = digest
        if set(recorded) != set(cheap_payloads) | {"SCRAMBLE.json"}:
            raise FileExistsError("existing manifest has an unexpected file set")
        for name in sorted(recorded):
            actual = hashlib.sha256((out / name).read_bytes()).hexdigest()
            if actual != recorded[name]:
                raise FileExistsError(f"existing protocol hash mismatch: {out / name}")
        return

    payloads = dict(cheap_payloads)
    payloads["SCRAMBLE.json"] = _json_bytes(scramble_descriptor_from_menus(train_menus))
    manifest = "".join(
        f"{hashlib.sha256(payloads[name]).hexdigest()}  {name}\n"
        for name in sorted(payloads)
    ).encode("ascii")
    payloads["MANIFEST_SHA256.txt"] = manifest

    out.mkdir(parents=True, exist_ok=False)
    for name, content in payloads.items():
        (out / name).write_bytes(content)


def _load_menu_jsonl(path: Path) -> list[Menu]:
    menus: list[Menu] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line:
            continue
        record = json.loads(line)
        if set(record) != {"canonical_id", "queries"}:
            raise ValueError(f"invalid menu record in {path}")
        menu = Menu(tuple(record["queries"]))
        if canonical_id(menu) != record["canonical_id"]:
            raise ValueError(f"canonical menu identity mismatch in {path}")
        menus.append(menu)
    return menus


def _implementation_commit() -> str:
    completed = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip()


def fit_artifact(protocol: str | Path, arm: str, out: str | Path) -> None:
    protocol = Path(protocol)
    out = Path(out)
    if arm not in {"learn", "scrambled", "frozen"}:
        raise ValueError("arm must be learn, scrambled, or frozen")

    verification = verify_protocol(protocol)
    hashes = verification.hashes

    resources = ResourceCounter()
    tracemalloc.start()
    started = time.perf_counter_ns()
    training_row_count = 0

    if arm == "frozen":
        theta = tuple(THETA0)
    elif arm == "scrambled":
        train_menus = _load_menu_jsonl(protocol / "TRAIN_MENUS.jsonl")
        rows = build_training_rows(train_menus, resources=resources)
        training_row_count = len(rows)
        expected = json.loads((protocol / "SCRAMBLE.json").read_text(encoding="utf-8"))
        actual = scramble_descriptor(rows)
        if actual != expected:
            raise ValueError("scramble descriptor does not match training rows")
        rows = scramble_feedback(rows)
        theta = fit_theta(rows, resources=resources)
    else:
        train_menus = _load_menu_jsonl(protocol / "TRAIN_MENUS.jsonl")
        rows = build_training_rows(train_menus, resources=resources)
        training_row_count = len(rows)
        theta = fit_theta(rows, resources=resources)

    out.parent.mkdir(parents=True, exist_ok=True)
    save_artifact(out, theta)
    wall_time_ns = time.perf_counter_ns() - started
    _, peak_python_bytes = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    artifact_bytes = out.stat().st_size
    report = resources.report(
        artifact_bytes=artifact_bytes,
        peak_python_bytes=peak_python_bytes,
        wall_time_ns=wall_time_ns,
    )
    receipt = {
        "schema": "arc-reactor-mkii-fit-receipt/v0",
        "implementation_commit": _implementation_commit(),
        "protocol_hashes": hashes,
        "protocol_manifest_sha256": verification.manifest_sha256,
        "arm": arm,
        "training_row_count": training_row_count,
        "resources": asdict(report),
        "artifact_sha256": hashlib.sha256(out.read_bytes()).hexdigest(),
    }
    receipt_path = out.with_name(out.name + ".receipt.json")
    receipt_path.write_bytes(_json_bytes(receipt))



def _fraction_json(value):
    return {"n": value.numerator, "d": value.denominator}


def _decision_record(decision):
    return {
        "candidate_mask": decision.candidate_mask,
        "remaining_budget": decision.remaining_budget,
        "scores": [
            {"query_id": query_id, "score": _fraction_json(score)}
            for query_id, score in decision.scores
        ],
        "chosen_query": decision.chosen_query,
    }


def _case_record(case):
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


def evaluate_artifacts(
    protocol: str | Path,
    learn_path: str | Path,
    scrambled_path: str | Path,
    frozen_path: str | Path,
    out: str | Path,
) -> None:
    protocol = Path(protocol)
    out = Path(out)
    if out.exists():
        raise FileExistsError(f"evaluation output already exists: {out}")

    verification = verify_protocol(protocol)
    menus = _load_menu_jsonl(protocol / "EVAL_MENUS.jsonl")

    artifact_paths = {
        "LEARN": Path(learn_path),
        "SCRAMBLED": Path(scrambled_path),
        "FROZEN": Path(frozen_path),
    }
    thetas = {name: load_artifact(path) for name, path in artifact_paths.items()}
    results = {
        name: evaluate_theta(name, theta, menus, artifact_bytes=artifact_paths[name].stat().st_size)
        for name, theta in thetas.items()
    }

    # Fresh-host replay checks. Only theta crosses the host boundary.
    transplant = {
        "theta_before_into_learn_host": transplant_equivalent(thetas["FROZEN"], thetas["FROZEN"], menus),
        "theta_after_into_frozen_host": transplant_equivalent(thetas["LEARN"], thetas["LEARN"], menus),
    }
    transplant["all_pass"] = all(transplant.values())

    planner_rows = []
    planner_counter = ResourceCounter()
    for menu in menus:
        task_id = canonical_id(menu)
        for budget in (2, 3):
            result = planner_reference(menu, budget, resources=planner_counter)
            planner_rows.append({
                "canonical_task_id": task_id,
                "budget": budget,
                "success_count": result.success_count,
                "states_expanded": result.states_expanded,
            })

    passed = ignition_pass(
        results["LEARN"],
        results["SCRAMBLED"],
        results["FROZEN"],
        transplant_ok=bool(transplant["all_pass"]),
    )

    out.mkdir(parents=True, exist_ok=False)
    for name in ("LEARN", "SCRAMBLED", "FROZEN"):
        payload = _jsonl_bytes([_case_record(case) for case in results[name].case_traces])
        (out / f"{name}_CASES.jsonl").write_bytes(payload)
    (out / "PLANNER_REFERENCE.jsonl").write_bytes(_jsonl_bytes(planner_rows))
    (out / "TRANSPLANT.json").write_bytes(_json_bytes(transplant))
    (out / "RESOURCES.json").write_bytes(
        _json_bytes({
            "LEARN": asdict(results["LEARN"].resources),
            "SCRAMBLED": asdict(results["SCRAMBLED"].resources),
            "FROZEN": asdict(results["FROZEN"].resources),
            "PLANNER": asdict(planner_counter.report()),
        })
    )
    (out / "SUMMARY.json").write_bytes(
        _json_bytes({
            "schema": "arc-reactor-mkii-evaluation-summary/v0",
            "protocol_manifest_sha256": verification.manifest_sha256,
            "ignition_pass": passed,
            "success_by_budget": {
                str(b): {name: results[name].success_by_budget[b] for name in ("LEARN", "SCRAMBLED", "FROZEN")}
                for b in (2, 3)
            },
        })
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="arc-mkii")
    sub = parser.add_subparsers(dest="command", required=True)

    freeze = sub.add_parser("freeze-protocol")
    freeze.add_argument("--out", required=True)

    fit = sub.add_parser("fit")
    fit.add_argument("--protocol", required=True)
    fit.add_argument("--arm", required=True, choices=("learn", "scrambled", "frozen"))
    fit.add_argument("--out", required=True)
    evaluate = sub.add_parser("evaluate")
    evaluate.add_argument("--protocol", required=True)
    evaluate.add_argument("--learn", required=True)
    evaluate.add_argument("--scrambled", required=True)
    evaluate.add_argument("--frozen", required=True)
    evaluate.add_argument("--out", required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "freeze-protocol":
        freeze_protocol(args.out)
        return 0
    if args.command == "fit":
        fit_artifact(args.protocol, args.arm, args.out)
        return 0
    if args.command == "evaluate":
        evaluate_artifacts(args.protocol, args.learn, args.scrambled, args.frozen, args.out)
        return 0
    raise SystemExit(f"command not implemented yet: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
