from app.models.workflow import Workflow, WorkflowStep


class PlannerAgent:
    def plan(self, workflow: Workflow) -> list[WorkflowStep]:
        return list(workflow.steps)
