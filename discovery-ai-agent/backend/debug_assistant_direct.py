import traceback
from app.db.session import SessionLocal
from app.api import discovery
from app.schemas.assistant import AssistantChatRequest
from app.models.discovery import ArtifactType

project_id = "62595a52-9e20-43e8-8c57-25aaacc67229"
db = SessionLocal()

try:
    print("=== DIRECT assistant_chat DEBUG ===")
    print("Project:", project_id)
    result = discovery.assistant_chat(
        project_id,
        AssistantChatRequest(
            message="@problem Сформулируй проблему: ручная подготовка Discovery занимает слишком много времени",
            artifact_type=ArtifactType.PROBLEM,
        ),
        db=db,
    )
    print("SUCCESS:")
    print(result)
except Exception:
    print("EXCEPTION:")
    traceback.print_exc()
finally:
    db.close()
