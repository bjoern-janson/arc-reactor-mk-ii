from pathlib import Path


def test_v2_g1_semantic_regression_script_is_bound_to_frozen_preflight_certificate():
    text = Path("scripts/v2_g1_v0_semantic_regression.py").read_text(encoding="utf-8")
    assert "078b3cfc948262bb71604a631e17972f8ad11a1f" in text
    assert "4aa007b39b060a954695b0d484a28723f9eb0c1949fc98e10c9c6c7ded4c20f0" in text
