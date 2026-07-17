from data_analyst_agent.tools.registry import ToolRegistry


def test_registry_exposes_registered_tools() -> None:
    registry = ToolRegistry()

    assert registry.list_tools() == ["run_sql", "generate_chart"]
    assert "run_sql" in registry.describe_tools()
