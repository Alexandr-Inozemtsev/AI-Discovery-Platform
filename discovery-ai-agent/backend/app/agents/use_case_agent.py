from app.agents.base_agent import BaseAgent


class UseCaseAgent(BaseAgent):
    artifact_type = "USE_CASES"

    def build_prompt(self, project, existing_artifacts: dict[str, str]) -> str:
        return f"Сформируй use cases для {project.project_name}"

    def _deterministic_result(self, project, existing_artifacts: dict[str, str]) -> str:
        return """# UC-01 Создание discovery-проекта
- **ID:** UC-01
- **Название:** Создание проекта
- **Основной актор:** Product Owner
- **Цель:** Инициировать discovery и заполнить метаданные проекта
- **Предусловия:** Пользователь открыл платформу
- **Триггер:** Нажата кнопка «Создать проект»
- **Основной сценарий:**
  1. PO вводит название проекта
  2. Система создаёт проект в статусе DRAFT
  3. Происходит переход в workspace
- **Альтернативные сценарии:** Название пустое → валидация
- **Исключения:** Ошибка сохранения БД
- **Постусловия:** Проект доступен в списке
- **Связанные требования:** FR-01, NFR-01
"""
