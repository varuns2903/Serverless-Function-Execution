import json
import tarfile
import io  # Add this import
import time
from .container_pool import ContainerPool

pool = ContainerPool()

async def execute_function(func: dict, payload: dict):
    start_time = time.time()
    errors = None
    resources = {"cpu": 0.1, "memory": "128Mi"}  # Placeholder

    try:
        container = pool.get_container(func["id"], func["language"], func["code"])
        
        # Prepare payload as a file
        payload_str = json.dumps(payload)
        tar_stream = io.BytesIO()
        with tarfile.open(fileobj=tar_stream, mode="w") as tar:
            payload_info = tarfile.TarInfo(name="payload.json")
            payload_info.size = len(payload_str)
            tar.addfile(payload_info, io.BytesIO(payload_str.encode()))
        tar_stream.seek(0)
        
        # Inject payload into container
        container.put_archive("/tmp", tar_stream)
        
        # Execute based on language
        if func["language"] == "python":
            cmd = ["python", "/tmp/function.py"]
        else:
            cmd = ["node", "/tmp/function.js"]
        
        exit_code, output = container.exec_run(cmd, stdin=True, stream=False)
        output = output.decode()
        
        if exit_code != 0:
            errors = output
            output = ""
        
        pool.release_container(container)
    except Exception as e:
        output = ""
        errors = str(e)
    
    response_time = time.time() - start_time
    return output, response_time, errors, resources