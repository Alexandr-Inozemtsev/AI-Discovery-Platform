from app.agents.base_agent import BaseAgent


class GoalAgent(BaseAgent):
    artifact_type = "GOAL"

    def build_prompt(self, project, existing_artifacts: dict[str, str]) -> str:
        return f"Сформируй SMART-цель для {project.project_name}"

    def _deterministic_result(self, project, existing_artifacts: dict[str, str]) -> str:
        return f"""# SMART-цель проекта
**S (Specific):** внедрить единый инструмент ведения discovery-проектов для «{project.project_name}».
**M (Measurable):** сократить время подготовки черновика БТ минимум на 30%.
**A (Achievable):** использовать текущую команду PO/BA и поэтапный rollout.
**R (Relevant):** цель напрямую влияет на скорость запуска продуктовых инициатив.
**T (Time-bound):** достичь целевого результата в течение 3 месяцев после внедрения.
"""
