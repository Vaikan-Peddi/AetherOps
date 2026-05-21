from app.connectors.base import connector_registry
from app.connectors.github_connector import GitHubConnector
from app.connectors.gmail_connector import GmailConnector
from app.connectors.slack_connector import SlackConnector

connector_registry.register(GmailConnector())
connector_registry.register(SlackConnector())
connector_registry.register(GitHubConnector())

__all__ = ["connector_registry"]
