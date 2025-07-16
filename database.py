from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# 請替換為您的 PostgreSQL 連接資訊
# 格式: "postgresql://user:password@host:port/dbname"
DATABASE_URL = "postgresql://sidep_user:tedke808387@localhost:5432/sidep_db"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Dependency to get the database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
