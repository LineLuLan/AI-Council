
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from config import settings

# Create engine using the URL from .env
# We add connect_args to force SSL, which Neon requires.
engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"sslmode": "require"} 
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()