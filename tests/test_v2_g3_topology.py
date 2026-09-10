from __future__ import annotations

from pathlib import Path

from arc_mkii.v2_g3_topology import verify_g4_topology


def test_g3_verifies_dormant_g4_trigger_and_custody_order_without_execution():
    result = verify_g4_topology(Path("."))
    assert result.trigger_branch == "run/v2-g4-official"
    assert result.lock_before_primary is True
    assert result.primary_before_autopsy is True
    assert result.no_automatic_g3_trigger is True


def test_g4_workflow_has_no_g3_freeze_trigger_and_orders_primary_before_autopsy():
    text = Path(".github/workflows/v2-g4-official-execution.yml").read_text(encoding="utf-8")
    header = text.split("permissions:", 1)[0]
    assert "run/v2-g4-official" in header
    assert "freeze/v2-g3-implementation" not in header
    assert "freeze/v2-g3-executable" not in header

    lock = text.index("Create exactly-once G4 start lock before first fit")
    primary_execute = text.index("Execute frozen primary V2 result after lock")
    primary_fossil = text.index("Fossilize primary scientific result before autopsy")
    autopsy = text.index("Compute post-primary nonacceptance root autopsy only after durable primary")
    autopsy_fossil = text.index("Fossilize downstream autopsy as direct child of primary")
    assert lock < primary_execute < primary_fossil < autopsy < autopsy_fossil


def test_g4_order_contract_forbids_result_work_during_g3():
    text = Path("experiments/v2/G4_EXECUTION_ORDER_CONTRACT.md").read_text(encoding="utf-8")
    assert "NO run/v2-g4-official branch" in text
    assert "NO G4 start lock" in text
    assert "NO V2 fit" in text
    assert "NO frozen-EVAL execution" in text
    assert "NO ignition" in text
    assert "NO real root-autopsy values" in text
