from app.assistant.intent_router import RoutedIntent
from app.models.discovery import ArtifactType, DiscoveryProject


class AssistantActionBuilder:
    def processor_metadata(
        self,
        *,
        project: DiscoveryProject,
        intent: RoutedIntent,
        artifact_type: ArtifactType,
        retrieval: dict,
        evidence: list,
        assumptions: list,
        open_questions: list,
        token_budget: dict,
        data_policy: dict,
    ) -> dict:
        return {
            "intent_type": intent.intent_type,
            "confidence": intent.confidence,
            "command": intent.command,
            "prompt_version": intent.prompt_version,
            "prompt_instruction": intent.instruction,
            "project_id": project.id,
            "target_artifact_type": artifact_type.value,
            "source": "ai_discovery_chat",
            "retrieval": retrieval,
            "evidence": evidence,
            "assumptions": assumptions,
            "open_questions": open_questions,
            "token_budget": token_budget,
            "data_policy": data_policy,
        }
