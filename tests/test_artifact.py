import json
from fractions import Fraction

import pytest

from arc_mkii.artifact import load_artifact, save_artifact
from arc_mkii.selector import THETA0


def test_artifact_round_trip_contains_only_schema_features_and_theta(tmp_path):
    path = tmp_path / "theta.json"
    save_artifact(path, tuple(Fraction(x) for x in THETA0))
    raw = json.loads(path.read_text())
    assert set(raw) == {"schema", "features", "theta"}
    assert load_artifact(path) == tuple(Fraction(x) for x in THETA0)


def test_artifact_rejects_unknown_top_level_state(tmp_path):
    path = tmp_path / "theta.json"
    save_artifact(path, tuple(Fraction(x) for x in THETA0))
    raw = json.loads(path.read_text())
    raw["cache"] = {"forbidden": True}
    path.write_text(json.dumps(raw))
    with pytest.raises(ValueError, match="top-level"):
        load_artifact(path)
