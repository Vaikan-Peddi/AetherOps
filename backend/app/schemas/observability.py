from pydantic import BaseModel


class ObservabilitySummary(BaseModel):
    total_documents: int
    total_queries: int
    total_workflows: int
    total_workflow_runs: int
