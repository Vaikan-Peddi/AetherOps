from pydantic import BaseModel


class TaskStatusResponse(BaseModel):
    task_id: str
    state: str
    ready: bool
    successful: bool
    failed: bool
    result: str | dict | list | None = None
