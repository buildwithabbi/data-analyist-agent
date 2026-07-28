"""Contracts that define which plan actions may invoke each tool."""

from pydantic import BaseModel

from .enums import StepAction


class ToolContract(BaseModel):
    tool: str
    supported_actions: set[StepAction]
    input_type: str
    output_type: str


TOOL_CONTRACTS = {
    "run_sql": ToolContract(
        tool="run_sql",
        supported_actions={StepAction.QUERY, StepAction.ANALYZE},
        input_type="SQLQuery",
        output_type="SQLResult",
    ),
    "generate_chart": ToolContract(
        tool="generate_chart",
        supported_actions={StepAction.GENERATE_CHART},
        input_type="DatasetArtifact",
        output_type="ChartResult",
    ),
}


def contract_for(tool: str | None) -> ToolContract | None:
    return TOOL_CONTRACTS.get(tool or "")
