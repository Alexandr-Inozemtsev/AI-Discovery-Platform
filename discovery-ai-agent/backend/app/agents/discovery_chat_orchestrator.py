from app.agents.intent_router import IntentRouter, RoutedIntent
from app.agents.runtime import StageProcessorResult, ToolAction, ToolPolicy
from app.models.discovery import ArtifactType, DiscoveryProject


class DiscoveryChatOrchestrator:
    def __init__(self, intent_router: IntentRouter | None = None, tool_policy: ToolPolicy | None = None):
        self.intent_router = intent_router or IntentRouter()
        self.tool_policy = tool_policy or ToolPolicy.for_ai_discovery_chat()

    def handle_message(
        self,
        *,
        project: DiscoveryProject,
        message: str,
        artifact_type: ArtifactType | None = None,
        context: dict | None = None,
    ) -> dict:
        intent = self.intent_router.route(message, artifact_type)
        if intent.intent_type == "draft_artifact_patch" and intent.target_artifact_type:
            result = self._draft_patch(project, message, intent)
        else:
            result = StageProcessorResult(
                ok=True,
                artifact_type=(intent.target_artifact_type.value if intent.target_artifact_type else ""),
                human_message="Я готов помочь пройти Discovery workflow. Уточните этап или артефакт, который нужно обновить.",
                metadata={"intent_type": intent.intent_type, "confidence": intent.confidence},
            )
        return {
            "intent": {
                "type": intent.intent_type,
                "target_artifact_type": intent.target_artifact_type.value if intent.target_artifact_type else None,
                "confidence": intent.confidence,
            },
            "result": result,
        }

    def _draft_patch(self, project: DiscoveryProject, message: str, intent: RoutedIntent) -> StageProcessorResult:
        artifact_type = intent.target_artifact_type
        if artifact_type is None:
            raise ValueError("target artifact type is required")
        for action_name in ("proposed_patch.create", "patch.preview"):
            if not self.tool_policy.is_allowed(ToolAction(name=action_name, target=artifact_type.value)):
                return StageProcessorResult(
                    ok=False,
                    artifact_type=artifact_type.value,
                    human_message="Действие запрещено политикой AI-чата.",
                    errors=[f"Tool action is not allowed: {action_name}"],
                    metadata={"intent_type": intent.intent_type},
                )

        proposed_patch = self._build_proposed_patch(artifact_type, message)
        changed_fields = list(proposed_patch.keys())
        preview = {
            "target_artifact_type": artifact_type.value,
            "changed_fields": changed_fields,
            "summary": f"Будут изменены поля: {', '.join(changed_fields)}.",
        }
        return StageProcessorResult(
            ok=True,
            artifact_type=artifact_type.value,
            content=self._content_from_patch(artifact_type, proposed_patch),
            structured_content=proposed_patch,
            proposed_patch=proposed_patch,
            preview=preview,
            human_message="Я подготовил черновик изменения. Проверьте preview перед применением.",
            metadata={
                "intent_type": intent.intent_type,
                "confidence": intent.confidence,
                "project_id": project.id,
                "source": "ai_discovery_chat",
            },
        )

    def _build_proposed_patch(self, artifact_type: ArtifactType, message: str) -> dict:
        clean_message = self._clean_message(message)
        if artifact_type == ArtifactType.PROBLEM:
            return {"problem_statement": clean_message}
        if artifact_type == ArtifactType.GOAL:
            return {"desired_outcome": clean_message}
        return {"content": clean_message}

    def _content_from_patch(self, artifact_type: ArtifactType, proposed_patch: dict) -> str:
        if artifact_type == ArtifactType.PROBLEM:
            return str(proposed_patch.get("problem_statement") or "")
        if artifact_type == ArtifactType.GOAL:
            return str(proposed_patch.get("desired_outcome") or "")
        return str(proposed_patch.get("content") or "")

    def _clean_message(self, message: str) -> str:
        text = (message or "").strip()
        for prefix in ("Сформулируй проблему:", "Проблема:", "problem:", "Goal:", "Цель:"):
            if text.lower().startswith(prefix.lower()):
                return text[len(prefix) :].strip()
        return text
