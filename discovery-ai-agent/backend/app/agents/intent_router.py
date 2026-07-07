from dataclasses import dataclass

from app.models.discovery import ArtifactType


@dataclass(frozen=True)
class RoutedIntent:
    intent_type: str
    target_artifact_type: ArtifactType | None
    confidence: float


class IntentRouter:
    def route(self, message: str, artifact_type: ArtifactType | None = None) -> RoutedIntent:
        if artifact_type is not None:
            return RoutedIntent("draft_artifact_patch", artifact_type, 1.0)

        normalized = (message or "").lower()
        if any(word in normalized for word in ("проблем", "problem")):
            return RoutedIntent("draft_artifact_patch", ArtifactType.PROBLEM, 0.8)
        if any(word in normalized for word in ("цель", "goal")):
            return RoutedIntent("draft_artifact_patch", ArtifactType.GOAL, 0.8)
        if any(word in normalized for word in ("проверь", "валидац", "validate")):
            return RoutedIntent("validate_workflow", None, 0.7)
        return RoutedIntent("explain_state", None, 0.6)
