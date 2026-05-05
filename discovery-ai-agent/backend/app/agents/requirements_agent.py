from app.agents.base_agent import BaseAgent


class RequirementsAgent(BaseAgent):
    artifact_type = "FUNCTIONAL_REQUIREMENTS"

    def build_prompt(self, project, existing_artifacts: dict[str, str]) -> str:
        return f"Сформируй требования для {project.project_name}"

    def _deterministic_result(self, project, existing_artifacts: dict[str, str]) -> str:
        return """# Функциональные требования
1. Система должна позволять создавать/редактировать discovery-проекты.
2. Система должна поддерживать генерацию артефактов mock-агентами.
3. Система должна хранить версионность артефактов.

# Нефункциональные требования
1. Время ответа API до 2 секунд для типовых операций.
2. Локальный запуск на Windows без Docker.
3. Устойчивость к повторным запросам генерации.

# Бизнес-правила
- Каждое сохранение артефакта увеличивает версию на 1.
- Генерация доступна только для поддерживаемых типов артефактов.

# Критерии приёмки
- PO может сгенерировать артефакт и увидеть обновлённую версию.
- Кнопка «Проверить» формирует валидационный отчёт.
"""
