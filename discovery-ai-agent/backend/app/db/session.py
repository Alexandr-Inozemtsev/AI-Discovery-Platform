from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "postgresql+psycopg2://postgres:postgres@db:5432/discovery"

engine = create_engine(DATABASE_URL, future=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    # Русский комментарий: базовая зависимость FastAPI для работы с БД в рамках запроса.
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
