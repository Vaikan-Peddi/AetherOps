from typing import Any

from app.connectors.base import ConnectorAction, connector_registry


class ExecutionAgent:
    async def execute_tool(self, connector_name: str, action_name: str, payload: dict[str, Any]) -> dict[str, Any]:
        connector = connector_registry.get(connector_name)
        return await connector.execute(ConnectorAction(name=action_name, payload=payload))
