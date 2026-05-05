from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.discovery import router as discovery_router

app = FastAPI(title="AI Discovery Agent API")

# Русский комментарий: разрешаем запросы с фронтенда Vite в локальной среде.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(discovery_router)


@app.get("/health")
def health():
    return {"status": "ok"}
