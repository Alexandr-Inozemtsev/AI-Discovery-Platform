from app.models.discovery import ArtifactType


CHAT_COMMAND_TEMPLATES = {
    "@context": {
        "intent_type": "draft_artifact_patch",
        "artifact_type": ArtifactType.CONTEXT,
        "prompt_version": "chat.context.v1",
        "instruction": "Проанализируй контекст, readiness, coverage и source_trace. Не считай metadata-only источники evidence.",
    },
    "@problem": {
        "intent_type": "draft_artifact_patch",
        "artifact_type": ArtifactType.PROBLEM,
        "prompt_version": "chat.problem.v1",
        "instruction": "Сформулируй проблему, боли, root causes и evidence. Если evidence нет, пометь вывод как assumption/open_question.",
    },
    "@goal": {
        "intent_type": "draft_artifact_patch",
        "artifact_type": ArtifactType.GOAL,
        "prompt_version": "chat.goal.v1",
        "instruction": "Предложи цель, SMART, KPI и assumptions. KPI без evidence должны быть open questions.",
    },
    "@business-effect": {
        "intent_type": "draft_artifact_patch",
        "artifact_type": ArtifactType.BUSINESS_EFFECT,
        "prompt_version": "chat.business_effect.v1",
        "instruction": "Оцени качественный и количественный эффект. Неподтверждённые метрики пометь как assumptions.",
    },
    "@use-cases": {
        "intent_type": "draft_artifact_patch",
        "artifact_type": ArtifactType.USE_CASES,
        "prompt_version": "chat.use_cases.v1",
        "instruction": "Сформируй use cases, flows, exceptions и linked requirements на основе evidence.",
    },
    "@requirements": {
        "intent_type": "draft_artifact_patch",
        "artifact_type": ArtifactType.FUNCTIONAL_REQUIREMENTS,
        "prompt_version": "chat.requirements.v1",
        "instruction": "Сформируй FR/NFR с acceptance criteria, evidence и assumption indicators.",
    },
    "@critic": {
        "intent_type": "validate_workflow",
        "artifact_type": ArtifactType.VALIDATION_REPORT,
        "prompt_version": "chat.critic.v1",
        "instruction": "Проверь качество, missing evidence, stale dependencies и unresolved assumptions.",
    },
    "@export": {
        "intent_type": "export_document",
        "artifact_type": ArtifactType.FINAL_BT,
        "prompt_version": "chat.export.v1",
        "instruction": "Подготовь Final BT/export summary и validation warnings перед DOCX.",
    },
}


def template_for_command(command: str) -> dict | None:
    return CHAT_COMMAND_TEMPLATES.get((command or "").strip().lower())
