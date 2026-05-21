from app.connectors.base import Connector, ConnectorAction


class GmailConnector(Connector):
    connector_name = "gmail"
    oauth_scopes = ["https://www.googleapis.com/auth/gmail.readonly"]

    async def execute(self, action: ConnectorAction) -> dict:
        return {"connector": self.connector_name, "action": action.name, "status": "placeholder"}
