from app.agents.base_agent import BaseAgent


class CriticAgent(BaseAgent):
    artifact_type = "VALIDATION_REPORT"

    def build_prompt(self, project, existing_artifacts: dict[str, str]) -> str:
        return f"Проверь качество артефактов проекта {project.project_name}"

    def _deterministic_result(self, project, existing_artifacts: dict[str, str]) -> str:
        filled = [k for k, v in existing_artifacts.items() if v.strip()]
        return f"""# Отчёт проверки Discovery
## Что заполнено хорошо
- Заполненные артефакты: {', '.join(filled) if filled else 'пока нет'}.

## Чего не хватает
- Метрик бизнес-эффекта с базовыми значениями.
- Явных критериев приёмки для ключевых use cases.

## Противоречия
- Возможна разница терминов между PROBLEM и REQUIREMENTS.

## Вопросы к PO
1. Какие KPI критичны для запуска?
2. Есть ли регуляторные ограничения?

## Рекомендации по доработке
- Согласовать глоссарий терминов.
- Уточнить границы MVP и этапа 2.
"""
