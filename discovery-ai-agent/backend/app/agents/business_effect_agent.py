from app.agents.base_agent import BaseAgent


class BusinessEffectAgent(BaseAgent):
    artifact_type = "BUSINESS_EFFECT"

    def build_prompt(self, project, existing_artifacts: dict[str, str]) -> str:
        return f"Сформируй бизнес-эффект для {project.project_name}"

    def _deterministic_result(self, project, existing_artifacts: dict[str, str]) -> str:
        return """# Ожидаемый бизнес-эффект
## Качественные эффекты
- Повышение прозрачности статуса discovery.
- Снижение числа противоречий в требованиях.
- Улучшение качества коммуникации между бизнесом и IT.

## Возможные количественные метрики
- Время подготовки артефактов: -25..35%.
- Количество итераций согласования БТ: -20%.
- Доля инициатив, ушедших в разработку без критических доработок: +15%.
"""
