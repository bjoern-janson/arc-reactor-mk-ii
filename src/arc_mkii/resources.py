from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ResourceCounter:
    training_rows_consumed: int = 0
    feature_vectors_computed: int = 0
    public_truth_table_bit_inspections: int = 0
    primitive_query_executions: int = 0
    terminal_actions: int = 0
    planner_states_expanded: int = 0

    def report(
        self,
        *,
        artifact_bytes: int = 0,
        peak_python_bytes: int = 0,
        wall_time_ns: int = 0,
    ) -> "ResourceReport":
        return ResourceReport(
            artifact_bytes=artifact_bytes,
            peak_python_bytes=peak_python_bytes,
            wall_time_ns=wall_time_ns,
            training_rows_consumed=self.training_rows_consumed,
            feature_vectors_computed=self.feature_vectors_computed,
            public_truth_table_bit_inspections=self.public_truth_table_bit_inspections,
            primitive_query_executions=self.primitive_query_executions,
            terminal_actions=self.terminal_actions,
            planner_states_expanded=self.planner_states_expanded,
        )


@dataclass(frozen=True)
class ResourceReport:
    artifact_bytes: int
    peak_python_bytes: int
    wall_time_ns: int
    training_rows_consumed: int
    feature_vectors_computed: int
    public_truth_table_bit_inspections: int
    primitive_query_executions: int
    terminal_actions: int
    planner_states_expanded: int
