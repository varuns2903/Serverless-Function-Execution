from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from .models import Base, Function, get_db, engine
from .crud import create_function, get_functions, get_function_by_id, get_function_by_route, update_function, delete_function
from .execution import execute_function
from .metrics import Metrics
from fastapi.routing import APIRoute
import logging

app = FastAPI()
metrics = Metrics()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)
    db = next(get_db())
    for func in get_functions(db):
        register_dynamic_route(func)

def register_dynamic_route(func: dict):
    route = func["route"]
    async def dynamic_endpoint(payload: dict, db: Session = Depends(get_db)):
        func_data = get_function_by_route(db, route)
        if not func_data:
            raise HTTPException(status_code=404, detail="Function not found")
        result, response_time, errors, resources = await execute_function(func_data, payload)
        metrics.record(route, response_time, errors, resources)
        return {"result": result}
    
    app.add_api_route(
        path=route,
        endpoint=dynamic_endpoint,
        methods=["POST"],
        response_model=dict,
        name=f"execute_{func['id']}"
    )
    logger.info(f"Registered dynamic route: {route}")

def remove_dynamic_route(route: str):
    app.routes[:] = [r for r in app.routes if not (isinstance(r, APIRoute) and r.path == route)]
    logger.info(f"Removed dynamic route: {route}")

@app.get("/")
async def root():
    return {"message": "Serverless Platform"}

@app.post("/functions/")
async def create_func(func: dict, db: Session = Depends(get_db)):
    result = create_function(db, func)
    register_dynamic_route(result)
    return result

@app.get("/functions/")
async def list_funcs(db: Session = Depends(get_db)):
    return get_functions(db)

@app.get("/functions/{func_id}")
async def read_func(func_id: int, db: Session = Depends(get_db)):
    func = get_function_by_id(db, func_id)
    if not func:
        raise HTTPException(status_code=404, detail="Function not found")
    return func

@app.put("/functions/{func_id}")
async def update_func(func_id: int, func: dict, db: Session = Depends(get_db)):
    result = update_function(db, func_id, func)
    if result:
        # Re-register route if it changed
        remove_dynamic_route(result["route"])  # Remove old route
        register_dynamic_route(result)  # Add new route
    return result

@app.delete("/functions/{func_id}")
async def delete_func(func_id: int, db: Session = Depends(get_db)):
    result = delete_function(db, func_id)
    if result and "route" in result:
        remove_dynamic_route(result["route"])
    return result

@app.post("/execute/{func_id}")
async def execute(func_id: int, payload: dict, db: Session = Depends(get_db)):
    func = get_function_by_id(db, func_id)
    if not func:
        raise HTTPException(status_code=404, detail="Function not found")
    result, response_time, errors, resources = await execute_function(func, payload)
    metrics.record(func["route"], response_time, errors, resources)
    return {"result": result}

@app.get("/metrics/")
async def get_metrics(route: str = None):
    return metrics.get_metrics(route)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)