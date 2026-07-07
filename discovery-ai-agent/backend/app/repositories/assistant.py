from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.assistant import AssistantAction, AssistantMessage, AssistantSession, AssistantToolRun


def create_session(db: Session, project_id: str, title: str = "AI Discovery Chat") -> AssistantSession:
    session = AssistantSession(project_id=project_id, title=title)
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def get_session(db: Session, project_id: str, session_id: str) -> AssistantSession | None:
    return db.scalars(
        select(AssistantSession).where(
            AssistantSession.project_id == project_id,
            AssistantSession.id == session_id,
        )
    ).first()


def list_sessions(db: Session, project_id: str) -> list[AssistantSession]:
    return db.scalars(
        select(AssistantSession)
        .where(AssistantSession.project_id == project_id)
        .order_by(AssistantSession.updated_at.desc())
    ).all()


def add_message(
    db: Session,
    *,
    project_id: str,
    session_id: str,
    role: str,
    content: str,
    payload: dict | None = None,
) -> AssistantMessage:
    message = AssistantMessage(
        project_id=project_id,
        session_id=session_id,
        role=role,
        content=content,
        payload=payload,
    )
    db.add(message)
    db.commit()
    db.refresh(message)
    return message


def list_messages(db: Session, project_id: str, session_id: str) -> list[AssistantMessage]:
    return db.scalars(
        select(AssistantMessage)
        .where(
            AssistantMessage.project_id == project_id,
            AssistantMessage.session_id == session_id,
        )
        .order_by(AssistantMessage.created_at.asc())
    ).all()


def add_action(
    db: Session,
    *,
    project_id: str,
    session_id: str,
    message_id: str | None,
    action_type: str,
    target_artifact_type: str | None,
    proposed_patch: dict | None,
    preview: dict | None,
    status: str = "proposed",
    action_metadata: dict | None = None,
) -> AssistantAction:
    action = AssistantAction(
        project_id=project_id,
        session_id=session_id,
        message_id=message_id,
        action_type=action_type,
        target_artifact_type=target_artifact_type,
        proposed_patch=proposed_patch,
        preview=preview,
        status=status,
        action_metadata=action_metadata,
    )
    db.add(action)
    db.commit()
    db.refresh(action)
    return action


def get_action(db: Session, project_id: str, session_id: str, action_id: str) -> AssistantAction | None:
    return db.scalars(
        select(AssistantAction).where(
            AssistantAction.project_id == project_id,
            AssistantAction.session_id == session_id,
            AssistantAction.id == action_id,
        )
    ).first()


def update_action(
    db: Session,
    action: AssistantAction,
    *,
    status: str | None = None,
    result: dict | None = None,
) -> AssistantAction:
    if status is not None:
        action.status = status
    if result is not None:
        action.result = result
    db.commit()
    db.refresh(action)
    return action


def add_tool_run(
    db: Session,
    *,
    project_id: str,
    session_id: str,
    action_id: str | None,
    tool_name: str,
    status: str,
    input_json: dict | None = None,
    output_json: dict | None = None,
    error_message: str | None = None,
) -> AssistantToolRun:
    tool_run = AssistantToolRun(
        project_id=project_id,
        session_id=session_id,
        action_id=action_id,
        tool_name=tool_name,
        status=status,
        input_json=input_json,
        output_json=output_json,
        error_message=error_message,
    )
    db.add(tool_run)
    db.commit()
    db.refresh(tool_run)
    return tool_run
