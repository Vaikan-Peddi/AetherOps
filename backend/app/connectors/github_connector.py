from app.connectors.base import Connector, ConnectorAction


class GitHubConnector(Connector):
    connector_name = "github"
    oauth_scopes = ["repo", "read:org"]

    async def execute(self, action: ConnectorAction) -> dict:
        return {"connector": self.connector_name, "action": action.name, "status": "placeholder"}
