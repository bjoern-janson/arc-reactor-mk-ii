from __future__ import annotations

import argparse

from .v2_g4_execution import compute_root_autopsy, execute_primary_result


def main() -> None:
    parser = argparse.ArgumentParser(description="ARC-MKII V2 G4 result-bearing execution")
    sub = parser.add_subparsers(dest="command", required=True)

    primary = sub.add_parser("primary")
    primary.add_argument("--protocol", default="experiments/v2/protocol")
    primary.add_argument("--out", required=True)
    primary.add_argument("--implementation-commit", required=True)
    primary.add_argument("--g4-start-lock-commit", required=True)

    autopsy = sub.add_parser("autopsy")
    autopsy.add_argument("--protocol", default="experiments/v2/protocol")
    autopsy.add_argument("--primary", required=True)
    autopsy.add_argument("--primary-record-commit", required=True)
    autopsy.add_argument("--out", required=True)

    args = parser.parse_args()
    if args.command == "primary":
        execute_primary_result(
            protocol_root=args.protocol,
            out=args.out,
            implementation_commit=args.implementation_commit,
            g4_start_lock_commit=args.g4_start_lock_commit,
        )
        return
    if args.command == "autopsy":
        compute_root_autopsy(
            protocol_root=args.protocol,
            primary_root=args.primary,
            primary_record_commit=args.primary_record_commit,
            out=args.out,
        )
        return
    raise SystemExit(2)


if __name__ == "__main__":
    main()
