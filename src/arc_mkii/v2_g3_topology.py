from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class G4TopologyVerification:
    trigger_branch: str
    lock_before_primary: bool
    primary_before_autopsy: bool
    no_automatic_g3_trigger: bool


def verify_g4_topology(repo_root: str | Path = ".") -> G4TopologyVerification:
    root = Path(repo_root)
    workflow_path = root / ".github/workflows/v2-g4-official-execution.yml"
    contract_path = root / "experiments/v2/G4_EXECUTION_ORDER_CONTRACT.md"
    execution_path = root / "src/arc_mkii/v2_g4_execution.py"
    cli_path = root / "src/arc_mkii/v2_g4_cli.py"
    for path in (workflow_path, contract_path, execution_path, cli_path):
        if not path.is_file():
            raise ValueError(f"required dormant G4 surface missing: {path}")

    workflow = workflow_path.read_text(encoding="utf-8")
    header = workflow.split("permissions:", 1)[0]
    if "- run/v2-g4-official" not in header:
        raise ValueError("G4 workflow lacks explicit run/v2-g4-official trigger")
    if "freeze/v2-g3-implementation" in header or "freeze/v2-g3-executable" in header:
        raise ValueError("G4 workflow is automatically triggerable by G3 freeze")

    markers = [
        "Verify no previous G4 lock or result fossil",
        "Create exactly-once G4 start lock before first fit",
        "Execute frozen primary V2 result after lock",
        "Fossilize primary scientific result before autopsy",
        "Compute post-primary nonacceptance root autopsy only after durable primary",
        "Fossilize downstream autopsy as direct child of primary",
    ]
    positions = [workflow.find(marker) for marker in markers]
    if any(position < 0 for position in positions):
        raise ValueError("G4 workflow is missing a frozen custody-order marker")
    if positions != sorted(positions) or len(set(positions)) != len(positions):
        raise ValueError("G4 workflow custody order drifted")

    contract = contract_path.read_text(encoding="utf-8")
    required_contract_terms = (
        "lock/v2-g4-started",
        "record/v2-g4-primary",
        "record/v2-g4-autopsy",
        "fresh-host serialized-artifact replay equivalence",
        "NO V2 fit",
        "NO frozen-EVAL execution",
    )
    if any(term not in contract for term in required_contract_terms):
        raise ValueError("G4 execution-order contract is incomplete")

    return G4TopologyVerification(
        trigger_branch="run/v2-g4-official",
        lock_before_primary=True,
        primary_before_autopsy=True,
        no_automatic_g3_trigger=True,
    )
