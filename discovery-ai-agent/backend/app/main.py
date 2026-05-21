from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.discovery import router as discovery_router
from app.api.error_handlers import install_error_handlers
from app.db.base import Base
from sqlalchemy import text

from app.db.session import engine
from app.models.llm_settings import LLMSettings
from app.db.session import SessionLocal

app = FastAPI(title="AI Discovery Agent API")
install_error_handlers(app)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def ensure_llm_settings_schema() -> None:
    expected = {
        "last_connection_status": "TEXT",
        "latency_ms": "INTEGER",
        "last_latency_ms": "INTEGER",
        "last_error": "TEXT",
        "last_actual_model": "TEXT",
        "last_checked_at": "DATETIME",
        "actual_model": "TEXT",
        "provider_response": "TEXT",
    }
    with engine.begin() as conn:
        cols = conn.execute(text("PRAGMA table_info(llm_settings)")).fetchall()
        names = {c[1] for c in cols}
        for col, typ in expected.items():
            if col not in names:
                conn.execute(text(f"ALTER TABLE llm_settings ADD COLUMN {col} {typ}"))


@app.on_event("startup")
def startup() -> None:
    Base.metadata.create_all(bind=engine)
    with engine.begin() as conn:
        cols = conn.execute(text("PRAGMA table_info(discovery_artifacts)")).fetchall()
        names = {c[1] for c in cols}
        if "structured_content" not in names:
            conn.execute(text("ALTER TABLE discovery_artifacts ADD COLUMN structured_content JSON"))
        if "rich_content_json" not in names:
            conn.execute(text("ALTER TABLE discovery_artifacts ADD COLUMN rich_content_json JSON"))
        if "rendered_html" not in names:
            conn.execute(text("ALTER TABLE discovery_artifacts ADD COLUMN rendered_html TEXT"))

    ensure_llm_settings_schema()

    env_path = Path(__file__).resolve().parents[2] / '.env'
    if not env_path.exists():
        env_path.write_text("""LLM_PROVIDER=mock
OPENROUTER_API_KEY=
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
OPENROUTER_MODEL=deepseek/deepseek-chat-v3-0324:free
LLM_TIMEOUT_SECONDS=120
LLM_TEMPERATURE=0.2
""")

    session = SessionLocal()
    try:
        if not session.query(LLMSettings).first():
            session.add(LLMSettings(provider='mock', base_url='https://openrouter.ai/api/v1', model='deepseek/deepseek-chat-v3-0324:free', api_key=None, timeout_seconds=120, temperature=0.2, is_active=True))
            session.commit()
    finally:
        session.close()


app.include_router(discovery_router)


@app.get("/health")
def health():
    return {"status": "ok"}
