from __future__ import annotations

import argparse
import json

from .v2_g3_execution import g3_verify


def main() -> None:
    parser = argparse.ArgumentParser(description="ARC-MKII V2 G3 non-result-bearing verifier")
    sub = parser.add_subparsers(dest="command", required=True)
    verify = sub.add_parser("verify")
    verify.add_argument("--protocol", default="experiments/v2/protocol")
    args = parser.parse_args()

    if args.command != "verify":
        raise SystemExit(2)

    report = g3_verify(args.protocol)
    print(
        json.dumps(
            {
                "status": "V2_G3_EXECUTABILITY_VERIFIED_NO_RESULT",
                "g2_protocol_manifest_sha256": report.g2.manifest_sha256,
                "train_rows": report.train.total_rows,
                "train_strata": [
                    {
                        "budget": budget,
                        "decision_depth": depth,
                        **report.train.strata[(budget, depth)],
                    }
                    for budget, depth in sorted(report.train.strata)
                ],
                "fit_performed": report.train.fit_performed,
                "eval_performed": report.train.eval_performed,
                "autopsy_performed": report.train.autopsy_performed,
                "ignition_computed": report.train.ignition_computed,
            },
            sort_keys=True,
            separators=(",", ":"),
        )
    )


if __name__ == "__main__":
    main()
