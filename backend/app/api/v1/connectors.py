from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.api.v1.deps import get_current_user
from app.connectors.base import ConnectorAction, connector_registry
from app.models.user import User

router = APIRouter(prefix="/connectors", tags=["connectors"])


class ConnectorExecuteRequest(BaseModel):
    action: str = Field(min_length=1)
    payload: dict = Field(default_factory=dict)


@router.get("")
def list_connectors(current_user: User = Depends(get_current_user)) -> dict:
    return {
        "connectors": [
            {
                "name": name,
                "oauth_scopes": connector_registry.get(name).oauth_scopes,
            }
            for name in connector_registry.list()
        ]
    }


@router.post("/{connector_name}/execute")
async def execute_connector(
    connector_name: str,
    payload: ConnectorExecuteRequest,
    current_user: User = Depends(get_current_user),
) -> dict:
    if connector_name not in connector_registry.list():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Connector not found")
    connector = connector_registry.get(connector_name)
    return await connector.execute(ConnectorAction(name=payload.action, payload=payload.payload))
