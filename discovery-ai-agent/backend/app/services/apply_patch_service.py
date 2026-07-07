from sqlalchemy.orm import Session

from app.agents.runtime import ToolAction, ToolPolicy
from app.api.errors import api_error
from app.models.assistant import AssistantAction
from app.models.discovery import ArtifactType
from app.repositories import assistant as assistant_repo
from app.repositories import discovery as discovery_repo


class ApplyPatchService:
    def __init__(self, tool_policy: ToolPolicy | None = None):
        self.tool_policy = tool_policy or ToolPolicy.for_ai_discovery_chat()

    def apply_action_patch(
        self,
        db: Session,
        *,
        project_id: str,
        session_id: str,
        action_id: str,
    ) -> dict:
        action = assistant_repo.get_action(db, project_id, session_id, action_id)
        if not action:
            raise api_error(404, "ARTIFACT_NOT_FOUND", "Действие AI-чата не найдено.")
        if action.status == "applied":
            raise api_error(400, "VALIDATION_ERROR", "Patch уже применён.")
        if not action.target_artifact_type or not action.proposed_patch:
            raise api_error(400, "VALIDATION_ERROR", "У действия нет patch для применения.")
        if not self.tool_policy.is_allowed(
            ToolAction(
                name="patch.apply",
                target=action.target_artifact_type,
                requires_user_confirmation=True,
            )
        ):
            raise api_error(403, "VALIDATION_ERROR", "Применение patch запрещено политикой AI-чата.")

        artifact_type = ArtifactType(action.target_artifact_type)
        previous = discovery_repo.get_artifact(db, project_id, artifact_type)
        structured = dict(previous.structured_content or {}) if previous else {}
        structured.update(action.proposed_patch)
        content = self._content_from_patch(artifact_type, structured, previous.content if previous else "")
        saved = discovery_repo.upsert_artifact(db, project_id, artifact_type, content, structured_content=structured)
        result = {
            "artifact_id": saved.id,
            "artifact_type": saved.artifact_type.value,
            "version": saved.version,
            "applied_patch": action.proposed_patch,
        }
        updated_action = assistant_repo.update_action(db, action, status="applied", result=result)
        assistant_repo.add_tool_run(
            db,
            project_id=project_id,
            session_id=session_id,
            action_id=action_id,
            tool_name="patch.apply",
            status="success",
            input_json={"target_artifact_type": action.target_artifact_type, "patch": action.proposed_patch},
            output_json=result,
        )
        return {"artifact": saved, "action": updated_action}

    def _content_from_patch(self, artifact_type: ArtifactType, structured: dict, previous_content: str) -> str:
        if artifact_type == ArtifactType.PROBLEM:
            return str(structured.get("problem_statement") or structured.get("main_problem") or previous_content or "")
        if artifact_type == ArtifactType.GOAL:
            return str(structured.get("desired_outcome") or structured.get("title") or previous_content or "")
        return str(structured.get("content") or previous_content or "")
