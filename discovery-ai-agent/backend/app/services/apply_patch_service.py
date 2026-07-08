import hashlib
import json

from sqlalchemy.orm import Session

from app.agents.runtime import ToolAction, ToolPolicy
from app.api.errors import api_error
from app.models.assistant import AssistantAction
from app.models.discovery import ArtifactType
from app.repositories import assistant as assistant_repo
from app.repositories import discovery as discovery_repo


AI_CHAT_APPLY_ARTIFACT_ALLOWLIST = {
    ArtifactType.PROBLEM.value,
    ArtifactType.GOAL.value,
    ArtifactType.BUSINESS_EFFECT.value,
    ArtifactType.USE_CASES.value,
    ArtifactType.FUNCTIONAL_REQUIREMENTS.value,
    ArtifactType.NON_FUNCTIONAL_REQUIREMENTS.value,
    ArtifactType.FINAL_BT.value,
}

AI_CHAT_PATCH_FIELD_ALLOWLIST = {
    ArtifactType.PROBLEM.value: {
        "problem_statement",
        "pains",
        "user_pains",
        "business_pains",
        "root_causes",
        "questions",
        "evidence_signals",
        "evidence",
        "assumptions",
        "open_questions",
        "source_trace",
    },
    ArtifactType.GOAL.value: {
        "recommended_goal",
        "desired_outcome",
        "title",
        "smart",
        "kpi",
        "successMetrics",
        "assumptions",
        "constraints",
        "evidence",
        "open_questions",
        "source_trace",
    },
    ArtifactType.BUSINESS_EFFECT.value: {
        "qualitative_effect",
        "quantitative_effect",
        "metrics",
        "open_questions",
        "evidence",
        "assumptions",
        "source_trace",
    },
    ArtifactType.USE_CASES.value: {
        "use_cases",
        "uc_cards",
        "flows",
        "exceptions",
        "linked_requirements",
        "evidence",
        "assumptions",
        "open_questions",
        "source_trace",
    },
    ArtifactType.FUNCTIONAL_REQUIREMENTS.value: {
        "functional_requirements",
        "requirements",
        "validation_warnings",
        "evidence",
        "assumptions",
        "open_questions",
        "source_trace",
    },
    ArtifactType.NON_FUNCTIONAL_REQUIREMENTS.value: {
        "non_functional_requirements",
        "validation_warnings",
        "evidence",
        "assumptions",
        "open_questions",
        "source_trace",
    },
    ArtifactType.FINAL_BT.value: {
        "document_preview",
        "validation_warnings",
        "export",
        "evidence",
        "assumptions",
        "open_questions",
        "source_trace",
    },
}


def build_patch_audit_summary(patch: dict | None) -> dict:
    safe_patch = patch if isinstance(patch, dict) else {}
    canonical = json.dumps(safe_patch, sort_keys=True, ensure_ascii=False, default=str)
    evidence = safe_patch.get("evidence") if isinstance(safe_patch.get("evidence"), list) else []
    assumptions = safe_patch.get("assumptions") if isinstance(safe_patch.get("assumptions"), list) else []
    open_questions = safe_patch.get("open_questions") if isinstance(safe_patch.get("open_questions"), list) else []
    return {
        "patch_hash": hashlib.sha256(canonical.encode("utf-8")).hexdigest(),
        "changed_fields": [
            key
            for key in safe_patch.keys()
            if key not in {"evidence", "assumptions", "open_questions", "source_trace"}
        ],
        "evidence_count": len(evidence),
        "assumption_count": len(assumptions),
        "open_question_count": len(open_questions),
        "has_evidence": bool(evidence),
    }


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
        if action.action_type != "proposed_patch":
            raise api_error(400, "VALIDATION_ERROR", "Можно применять только proposed_patch.")
        if action.status not in {"proposed", "previewed"}:
            raise api_error(400, "VALIDATION_ERROR", "Patch нельзя применить в текущем статусе.")
        if not action.target_artifact_type or not action.proposed_patch:
            raise api_error(400, "VALIDATION_ERROR", "У действия нет patch для применения.")
        if action.target_artifact_type not in AI_CHAT_APPLY_ARTIFACT_ALLOWLIST:
            raise api_error(403, "VALIDATION_ERROR", "AI Chat не может применять patch к этому типу артефакта.")
        if not self.tool_policy.is_allowed(
            ToolAction(
                name="patch.apply",
                target=action.target_artifact_type,
                requires_user_confirmation=True,
            )
        ):
            raise api_error(403, "VALIDATION_ERROR", "Применение patch запрещено политикой AI-чата.")

        artifact_type = ArtifactType(action.target_artifact_type)
        forbidden_fields = sorted(set(action.proposed_patch.keys()) - AI_CHAT_PATCH_FIELD_ALLOWLIST[artifact_type.value])
        if forbidden_fields:
            raise api_error(
                400,
                "VALIDATION_ERROR",
                "Patch содержит поля, запрещённые для этого типа артефакта.",
                {"forbidden_fields": forbidden_fields},
            )
        previous = discovery_repo.get_artifact(db, project_id, artifact_type)
        expected_version = (action.action_metadata or {}).get("base_artifact_version")
        current_version = previous.version if previous else 0
        if expected_version is not None and int(expected_version) != current_version:
            raise api_error(
                409,
                "VERSION_CONFLICT",
                "Артефакт изменился после preview. Обновите preview и попробуйте снова.",
                {"expected_version": expected_version, "current_version": current_version},
            )
        structured = dict(previous.structured_content or {}) if previous else {}
        structured.update(action.proposed_patch)
        content = self._content_from_patch(artifact_type, structured, previous.content if previous else "")
        saved = discovery_repo.upsert_artifact(db, project_id, artifact_type, content, structured_content=structured)
        audit_summary = build_patch_audit_summary(action.proposed_patch)
        result = {
            "artifact_id": saved.id,
            "artifact_type": saved.artifact_type.value,
            "version": saved.version,
            **audit_summary,
        }
        updated_action = assistant_repo.update_action(db, action, status="applied", result=result)
        assistant_repo.add_tool_run(
            db,
            project_id=project_id,
            session_id=session_id,
            action_id=action_id,
            tool_name="patch.apply",
            status="success",
            input_json={
                "target_artifact_type": action.target_artifact_type,
                "patch_hash": audit_summary["patch_hash"],
                "changed_fields": audit_summary["changed_fields"],
            },
            output_json=result,
        )
        return {"artifact": saved, "action": updated_action}

    def _content_from_patch(self, artifact_type: ArtifactType, structured: dict, previous_content: str) -> str:
        if artifact_type == ArtifactType.PROBLEM:
            return str(structured.get("problem_statement") or structured.get("main_problem") or previous_content or "")
        if artifact_type == ArtifactType.GOAL:
            return str(structured.get("desired_outcome") or structured.get("title") or previous_content or "")
        return str(structured.get("content") or previous_content or "")
