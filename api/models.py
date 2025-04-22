from sqlalchemy import Column, Integer, String, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "sqlite:///functions.db"  # Use PostgreSQL in production, e.g., "postgresql://user:password@localhost/dbname"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Function(Base):
    __tablename__ = "functions"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    language = Column(String)
    code = Column(String)
    timeout = Column(Integer)
    route = Column(String, unique=True, index=True)
    runtime = Column(String, default="runc")  # Ensure this is present

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()