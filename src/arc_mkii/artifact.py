from __future__ import annotations

import json
from fractions import Fraction
from pathlib import Path
from typing import Iterable

from .features import FEATURE_NAMES

SCHEMA = "arc-reactor-mkii-selector/v0"
_ALLOWED_KEYS = {"schema", "features", "theta"}


def _fraction_record(value: Fraction) -> dict[str, int]:
    return {"n": value.numerator, "d": value.denominator}


def save_artifact(path: str | Path, theta: Iterable[Fraction]) -> None:
    values = tuple(Fraction(value) for value in theta)
    if len(values) != 8:
        raise ValueError("theta must contain eight coefficients")
    record = {
        "schema": SCHEMA,
        "features": list(FEATURE_NAMES),
        "theta": [_fraction_record(value) for value in values],
    }
    Path(path).write_text(
        json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def load_artifact(path: str | Path) -> tuple[Fraction, ...]:
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(raw, dict) or set(raw) != _ALLOWED_KEYS:
        raise ValueError("artifact top-level keys must be exactly schema, features, theta")
    if raw["schema"] != SCHEMA:
        raise ValueError("artifact schema mismatch")
    if tuple(raw["features"]) != FEATURE_NAMES:
        raise ValueError("artifact feature order mismatch")
    theta_raw = raw["theta"]
    if not isinstance(theta_raw, list) or len(theta_raw) != 8:
        raise ValueError("artifact theta must contain eight coefficients")
    values: list[Fraction] = []
    for item in theta_raw:
        if not isinstance(item, dict) or set(item) != {"n", "d"}:
            raise ValueError("coefficient must contain numerator and denominator")
        numerator = item["n"]
        denominator = item["d"]
        if not isinstance(numerator, int) or not isinstance(denominator, int):
            raise ValueError("coefficient numerator and denominator must be integers")
        if denominator <= 0:
            raise ValueError("coefficient denominator must be positive")
        values.append(Fraction(numerator, denominator))
    return tuple(values)
