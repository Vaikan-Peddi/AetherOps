from pydantic import BaseModel, Field


class ObservabilitySummary(BaseModel):
    model_config = {"protected_namespaces": ()}

    total_documents: int
    total_queries: int
    total_workflows: int
    total_workflow_runs: int
    avg_latency_ms: float = 0
    total_tokens: int = 0
    provider_usage: dict[str, int] = Field(default_factory=dict)
    model_distribution: dict[str, int] = Field(default_factory=dict)
    workflow_status: dict[str, int] = Field(default_factory=dict)
