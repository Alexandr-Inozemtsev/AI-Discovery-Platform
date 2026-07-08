from app.models.discovery import ArtifactType
from app.processors.requirements_processor import RequirementsProcessor
from app.processors.stage_draft_processor import StageDraftProcessor
from app.processors.validation_processor import ValidationProcessor


def processor_for_artifact(artifact_type: ArtifactType | str) -> StageDraftProcessor | RequirementsProcessor | ValidationProcessor | None:
    value = artifact_type.value if isinstance(artifact_type, ArtifactType) else str(artifact_type)
    if value in StageDraftProcessor.supported_artifact_types:
        return StageDraftProcessor()
    if value in RequirementsProcessor.supported_artifact_types:
        return RequirementsProcessor()
    if value in ValidationProcessor.supported_artifact_types:
        return ValidationProcessor()
    return None


__all__ = [
    "RequirementsProcessor",
    "StageDraftProcessor",
    "ValidationProcessor",
    "processor_for_artifact",
]
