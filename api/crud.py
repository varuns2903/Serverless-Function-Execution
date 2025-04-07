from sqlalchemy.orm import Session
from .models import Function

def create_function(db: Session, func: dict):
    db_func = Function(**func)
    db.add(db_func)
    db.commit()
    db.refresh(db_func)
    return db_func.__dict__

def get_functions(db: Session):
    return [func.__dict__ for func in db.query(Function).all()]

def get_function(db: Session, func_id: int):
    func = db.query(Function).filter(Function.id == func_id).first()
    return func.__dict__ if func else None

def update_function(db: Session, func_id: int, func: dict):
    print("Updating....")
    db_func = db.query(Function).filter(Function.id == func_id).first()
    if not db_func:
        return None
    for key, value in func.items():
        setattr(db_func, key, value)
    db.commit()
    db.refresh(db_func)
    return db_func.__dict__

def delete_function(db: Session, func_id: int):
    db_func = db.query(Function).filter(Function.id == func_id).first()
    if not db_func:
        return None
    db.delete(db_func)
    db.commit()
    return {"status": "deleted"}