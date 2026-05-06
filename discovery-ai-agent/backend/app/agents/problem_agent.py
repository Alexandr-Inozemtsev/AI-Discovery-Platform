from app.agents.base_agent import BaseAgent


class ProblemAgent(BaseAgent):
    artifact_type = "PROBLEM"

    def build_prompt(self, project, existing_artifacts: dict[str, str]) -> str:
        return f"Сформируй PROBLEM для проекта {project.project_name}. Контекст: {existing_artifacts.get('CONTEXT', 'не заполнен')}"

    def _deterministic_result(self, project, existing_artifacts: dict[str, str]) -> str:
        return f"""# Описание проблемы
Текущий процесс в проекте «{project.project_name}» содержит ручные и несогласованные шаги.

## Причины
1. Отсутствует единая точка управления discovery-артефактами.
2. Информация хранится в разрозненных источниках.
3. Нет стандарта качества формулировок требований.

## Последствия
- Задержки в подготовке бизнес-требований.
- Рост количества уточнений на этапах согласования.
- Повышенная нагрузка на PO и аналитиков.

## Кого затрагивает
- Product Owner
- Бизнес-аналитик
- Архитектор
- Команда разработки

## Почему требуется изменение
Нужен управляемый контур discovery, который сокращает цикл от идеи до согласованного БТ.
"""
