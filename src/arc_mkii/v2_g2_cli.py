from __future__ import annotations

import argparse
from pathlib import Path

from .v2_g2_protocol import freeze_v2_protocol, verify_v2_protocol


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m arc_mkii.v2_g2_cli")
    subparsers = parser.add_subparsers(dest="command", required=True)

    freeze = subparsers.add_parser("freeze", help="constitute the frozen V2 G2 protocol")
    freeze.add_argument("--g1-root", type=Path, required=True)
    freeze.add_argument("--out", type=Path, required=True)

    verify = subparsers.add_parser("verify", help="verify frozen V2 G2 protocol custody")
    verify.add_argument("--g1-root", type=Path, required=True)
    verify.add_argument("--protocol", type=Path, required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "freeze":
        freeze_v2_protocol(args.g1_root, args.out)
        return 0
    if args.command == "verify":
        verify_v2_protocol(args.g1_root, args.protocol)
        return 0
    raise RuntimeError("unreachable G2 command")


if __name__ == "__main__":
    raise SystemExit(main())
