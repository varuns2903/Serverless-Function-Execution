import docker
import asyncio
import tarfile
import io
from .container_pool import ContainerPool

pool = ContainerPool()
client = docker.from_env()

async def execute_function(func, payload):
    container = pool.get_container(func.id, func.language, func.code)
    try:
        start_time = asyncio.get_event_loop().time()
        
        if func.language == "python":
            temp_file = "/tmp/script.py"
            # Create a tar archive with the code
            code_bytes = func.code.encode('utf-8')
            tar_stream = io.BytesIO()
            with tarfile.open(fileobj=tar_stream, mode="w") as tar:
                tarinfo = tarfile.TarInfo(name="script.py")
                tarinfo.size = len(code_bytes)
                tar.addfile(tarinfo, io.BytesIO(code_bytes))
            tar_stream.seek(0)
            container.put_archive("/tmp", tar_stream)
            cmd = f"python {temp_file}"
        elif func.language == "javascript":
            temp_file = "/tmp/script.js"
            code_bytes = func.code.encode('utf-8')
            tar_stream = io.BytesIO()
            with tarfile.open(fileobj=tar_stream, mode="w") as tar:
                tarinfo = tarfile.TarInfo(name="script.js")
                tarinfo.size = len(code_bytes)
                tar.addfile(tarinfo, io.BytesIO(code_bytes))
            tar_stream.seek(0)
            container.put_archive("/tmp", tar_stream)
            cmd = f"node {temp_file}"
        else:
            raise ValueError(f"Unsupported language: {func.language}")
        
        print(f"Executing command: {cmd}")  # Debug log for execution
        exec_result = await asyncio.to_thread(container.exec_run, cmd)
        response_time = asyncio.get_event_loop().time() - start_time
        
        if exec_result.exit_code != 0:
            return exec_result.output.decode(), response_time, f"Error: {exec_result.output.decode()}", {"cpu": "unknown"}
        return exec_result.output.decode(), response_time, None, {"cpu": "unknown"}
    except asyncio.TimeoutError:
        container.kill()
        return "Timeout", response_time, "timeout", {"cpu": "unknown"}
    except Exception as e:
        return "Error", response_time, str(e), {"cpu": "unknown"}