from app.connectors.base import Connector, ConnectorAction


class SlackConnector(Connector):
    connector_name = "slack"
    oauth_scopes = ["channels:read", "chat:write"]

    async def execute(self, action: ConnectorAction) -> dict:
        return {"connector": self.connector_name, "action": action.name, "status": "placeholder"}
