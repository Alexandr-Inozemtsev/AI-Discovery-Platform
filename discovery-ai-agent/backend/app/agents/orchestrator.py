from app.agents.business_effect_agent import BusinessEffectAgent
from app.agents.goal_agent import GoalAgent
from app.agents.problem_agent import ProblemAgent
from app.agents.requirements_agent import RequirementsAgent
from app.agents.use_case_agent import UseCaseAgent
from app.llm.mock_client import MockLLMClient


class AgentOrchestrator:
    def __init__(self, llm=None):
        llm = llm or MockLLMClient()
        self._agents = {
            "PROBLEM": ProblemAgent(llm),
            "GOAL": GoalAgent(llm),
            "BUSINESS_EFFECT": BusinessEffectAgent(llm),
            "USE_CASES": UseCaseAgent(llm),
            "FUNCTIONAL_REQUIREMENTS": RequirementsAgent(llm),
            "NON_FUNCTIONAL_REQUIREMENTS": RequirementsAgent(llm),
            "FINAL_BT": RequirementsAgent(llm),
        }

    def get_agent(self, artifact_type: str):
        return self._agents.get(artifact_type)
