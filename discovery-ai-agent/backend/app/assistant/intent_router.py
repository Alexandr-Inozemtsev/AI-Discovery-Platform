from dataclasses import dataclass

from app.assistant.prompt_templates import template_for_command
from app.models.discovery import ArtifactType


@dataclass(frozen=True)
class RoutedIntent:
    intent_type: str
    target_artifact_type: ArtifactType | None
    confidence: float
    command: str | None = None
    prompt_version: str = ""
    instruction: str = ""


class IntentRouter:
    def route(self, message: str, artifact_type: ArtifactType | None = None) -> RoutedIntent:
        normalized = (message or "").strip().lower()
        command = normalized.split()[0] if normalized.startswith("@") else ""
        template = template_for_command(command)
        if template:
            target = template["artifact_type"]
            return RoutedIntent(
                intent_type=template["intent_type"],
                target_artifact_type=target,
                confidence=1.0,
                command=command,
                prompt_version=template["prompt_version"],
                instruction=template["instruction"],
            )

        if artifact_type is not None:
            return RoutedIntent("draft_artifact_patch", artifact_type, 1.0)

        if any(word in normalized for word in ("проблем", "problem")):
            return RoutedIntent("draft_artifact_patch", ArtifactType.PROBLEM, 0.8)
        if any(word in normalized for word in ("цель", "goal")):
            return RoutedIntent("draft_artifact_patch", ArtifactType.GOAL, 0.8)
        if any(word in normalized for word in ("контекст", "context")):
            return RoutedIntent("draft_artifact_patch", ArtifactType.CONTEXT, 0.8)
        if any(word in normalized for word in ("требован", "requirements")):
            return RoutedIntent("draft_artifact_patch", ArtifactType.FUNCTIONAL_REQUIREMENTS, 0.8)
        if any(word in normalized for word in ("проверь", "валидац", "validate")):
            return RoutedIntent("validate_workflow", None, 0.7)
        return RoutedIntent("explain_state", None, 0.6)
