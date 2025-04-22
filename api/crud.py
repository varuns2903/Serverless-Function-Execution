from sqlalchemy.orm import Session
from .models import Function
import uuid

def create_function(db: Session, func: dict):
    # Exclude both 'id' and 'route' from initial creation
    db_func = Function(**{k: v for k, v in func.items() if k not in ["id", "route"]})
    db.add(db_func)
    db.commit()
    db.refresh(db_func)
    # Set route after ID is assigned
    unique_id = str(uuid.uuid4())
    user_specified = func.get("route", "").strip("/") or ""
    db_func.route = f"/fn/{unique_id}/{user_specified}"
    db.commit()
    db.refresh(db_func)
    return db_func.__dict__

def get_functions(db: Session):
    return [func.__dict__ for func in db.query(Function).all()]

def get_function_by_id(db: Session, func_id: int):
    func = db.query(Function).filter(Function.id == func_id).first()
    return func.__dict__ if func else None

def get_function_by_route(db: Session, route: str):
    func = db.query(Function).filter(Function.route == route).first()
    return func.__dict__ if func else None

def update_function(db: Session, func_id: int, func: dict):
    db_func = db.query(Function).filter(Function.id == func_id).first()
    if not db_func:
        return None
    for key, value in func.items():
        if key != "route":  # Handle route separately
            setattr(db_func, key, value)
    if "route" in func:
        unique_id = db_func.route.split("/")[2]
        user_specified = func["route"].strip("/") or ""
        db_func.route = f"/fn/{unique_id}/{user_specified}"
    db.commit()
    db.refresh(db_func)
    return db_func.__dict__

def delete_function(db: Session, func_id: int):
    db_func = db.query(Function).filter(Function.id == func_id).first()
    if not db_func:
        return None
    route = db_func.route
    db.delete(db_func)
    db.commit()
    return {"status": "deleted", "route": route}