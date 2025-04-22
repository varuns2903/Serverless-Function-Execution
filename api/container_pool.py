import docker
import io  # Add this import
import tarfile

class ContainerPool:
    def __init__(self):
        self.client = docker.from_env()
        self.containers = {}

    def get_container(self, func_id, language, code):
        # Create or reuse container
        container_key = f"{func_id}_{language}"
        if container_key in self.containers:
            return self.containers[container_key]
        
        # Create new container
        image = "python:3.12-slim" if language == "python" else "node:20-slim"
        container = self.client.containers.run(
            image,
            command="tail -f /dev/null",  # Keep container running
            detach=True,
            mem_limit="128m",
            cpu_shares=256
        )
        
        # Inject code
        tar_stream = io.BytesIO()
        with tarfile.open(fileobj=tar_stream, mode="w") as tar:
            code_info = tarfile.TarInfo(name="function.py" if language == "python" else "function.js")
            code_info.size = len(code)
            tar.addfile(code_info, io.BytesIO(code.encode()))
        tar_stream.seek(0)
        container.put_archive("/tmp", tar_stream)
        
        self.containers[container_key] = container
        return container

    def release_container(self, container):
        # Keep container for reuse (cleanup on shutdown if needed)
        pass