from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ConnectorAction:
    name: str
    payload: dict[str, Any]


class Connector(ABC):
    connector_name: str
    oauth_scopes: list[str] = []

    @abstractmethod
    async def execute(self, action: ConnectorAction) -> dict[str, Any]:
        """Execute a connector action. OAuth credential loading lands in a later phase."""


class ConnectorRegistry:
    def __init__(self) -> None:
        self._connectors: dict[str, Connector] = {}

    def register(self, connector: Connector) -> None:
        self._connectors[connector.connector_name] = connector

    def get(self, name: str) -> Connector:
        return self._connectors[name]

    def list(self) -> list[str]:
        return sorted(self._connectors.keys())


connector_registry = ConnectorRegistry()
