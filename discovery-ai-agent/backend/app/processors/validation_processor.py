from app.agents.runtime import StageProcessorRequest, StageProcessorResult
from app.models.discovery import ArtifactType


class ValidationProcessor:
    supported_artifact_types = {ArtifactType.VALIDATION_REPORT.value}

    def process(self, request: StageProcessorRequest) -> StageProcessorResult:
        if request.contains_secret_fields():
            return StageProcessorResult(
                ok=False,
                artifact_type=request.artifact_type,
                human_message="Запрос содержит поля, похожие на секреты. Уберите credentials и повторите запрос.",
                errors=["Secret-like fields are not allowed in StageProcessorRequest."],
            )

        artifacts = request.input_artifacts or {}
        warnings = []
        blockers = []
        required = (ArtifactType.PROBLEM.value, ArtifactType.GOAL.value, ArtifactType.FUNCTIONAL_REQUIREMENTS.value)
        for artifact_type in required:
            artifact = artifacts.get(artifact_type) or {}
            structured_keys = artifact.get("structured_keys") if isinstance(artifact, dict) else []
            if not structured_keys:
                blockers.append(f"Артефакт {artifact_type} не содержит структурированных полей.")
        if not artifacts:
            warnings.append("Нет артефактов для проверки качества Discovery workflow.")

        report = {
            "validation_status": "requires_attention" if blockers or warnings else "ready",
            "warnings": warnings or ["Проверьте evidence, assumptions и открытые вопросы перед экспортом."],
            "blockers": blockers,
            "checked_artifacts": sorted(artifacts.keys()),
            "quality_gates": {
                "has_problem": ArtifactType.PROBLEM.value in artifacts,
                "has_goal": ArtifactType.GOAL.value in artifacts,
                "has_requirements": ArtifactType.FUNCTIONAL_REQUIREMENTS.value in artifacts,
            },
        }
        return StageProcessorResult(
            ok=True,
            artifact_type=ArtifactType.VALIDATION_REPORT.value,
            content="Проверка качества Discovery workflow выполнена.",
            structured_content=report,
            proposed_patch={},
            preview={},
            warnings=report["warnings"],
            errors=blockers,
            human_message="Я проверил качество Discovery workflow. Изменения в артефакты не применялись.",
            metadata={"processor": "validation_processor"},
        )
