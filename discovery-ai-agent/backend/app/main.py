from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.discovery import router as discovery_router
from app.db.base import Base
from app.db.session import engine

app = FastAPI(title="AI Discovery Agent API")

# Русский комментарий: CORS для фронтенда Vite на локальном порту.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup() -> None:
    # Русский комментарий: при старте автоматически создаём таблицы SQLite, если их ещё нет.
    Base.metadata.create_all(bind=engine)


app.include_router(discovery_router)


@app.get("/health")
def health():
    return {"status": "ok"}
