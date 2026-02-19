
import docker
import os
import shutil
import time
import json
import base64
from typing import Dict

class DockerManager:
    def __init__(self):
        try:
            self.client = docker.from_env()
        except Exception as e:
            print(f"Docker Error: {e}")
            self.client = None

    def build_sandbox_image(self):
        """
        Builds the universal sandbox image if not present.
        """
        if not self.client: return False
        
        try:
            print("Building Universal Sandbox Image (this may take time)...")
            # Point to backend/sandbox.Dockerfile
            dockerfile_path = os.path.join(os.path.dirname(__file__), "sandbox.Dockerfile")
            self.client.images.build(
                path=os.path.dirname(__file__),
                dockerfile="sandbox.Dockerfile",
                tag="rift-sandbox:latest"
            )
            print("Sandbox Image Built Successfully.")
            return True
        except Exception as e:
            print(f"Build Failed: {e}")
            return False

    def run_tests_in_sandbox(self, repo_url: str, branch_name: str, token: str, auth_mode: str = "https", private_key: str = None) -> Dict:
        """
        Runs tests in a Docker container using Universal Runner.
        """
        if not self.client:
            return {"status": "ERROR", "logs": "Docker not available."}

        # Check for image
        try:
            self.client.images.get("rift-sandbox:latest")
        except docker.errors.ImageNotFound:
            if not self.build_sandbox_image():
                return {"status": "ERROR", "logs": "Failed to build sandbox image."}

        container = None
        try:
            clean_url = repo_url.replace("https://", "")
            
            # 1. Prepare Clone Command
            clone_cmd = ""
            pre_config = ""
            
            if auth_mode == "https":
                if token:
                     auth_url = f"https://{token}@{clean_url}"
                else:
                     auth_url = repo_url
                clone_cmd = f"git clone {auth_url} /app/repo"
                
            elif auth_mode == "ssh":
                if not private_key:
                     return {"status": "ERROR", "logs": "Private Key missing for SSH mode."}
                     
                b64_key = base64.b64encode(private_key.encode('utf-8')).decode('utf-8')
                
                pre_config = f"""
                mkdir -p /root/.ssh && \
                echo '{b64_key}' | base64 -d > /root/.ssh/id_rsa && \
                chmod 600 /root/.ssh/id_rsa && \
                ssh-keyscan github.com >> /root/.ssh/known_hosts && \
                """
                
                ssh_url = repo_url
                if "https://" in repo_url:
                     ssh_url = repo_url.replace("https://github.com/", "git@github.com:")
                
                clone_cmd = f"git clone {ssh_url} /app/repo"

            # 2. Inject Universal Runner Script
            # Read script content
            runner_path = os.path.join(os.path.dirname(__file__), "scripts", "universal_runner.py")
            with open(runner_path, "r") as f:
                runner_content = f.read()
            
            b64_runner = base64.b64encode(runner_content.encode('utf-8')).decode('utf-8')

            # 3. Execution Script
            script = f"""
            {pre_config}
            {clone_cmd} && \
            cd /app/repo && \
            git checkout {branch_name} || git checkout -b {branch_name} && \
            echo '{b64_runner}' | base64 -d > /app/universal_runner.py && \
            python3 /app/universal_runner.py && \
            rm -rf /root/.ssh/id_rsa
            """
            
            container = self.client.containers.run(
                "rift-sandbox:latest",
                command=f"bash -c '{script}'",
                detach=True,
                remove=False
            )
            
            exit_code = container.wait()
            logs = container.logs().decode("utf-8")
            container.remove()

            # 4. Parse JSON Output
            # The runner outputs JSON at the end, but logs might contain other stuff.
            # Look for the last line or JSON block.
            try:
                # Find start of JSON
                json_start = logs.rfind('{')
                if json_start != -1:
                    json_str = logs[json_start:]
                    result = json.loads(json_str)
                    
                    # Add raw logs if missing or just keep full logs
                    if "raw_logs" not in result or not result["raw_logs"]:
                         result["raw_logs"] = logs
                    
                    # Mask Token
                    if token:
                        result["raw_logs"] = result["raw_logs"].replace(token, "***TOKEN***")
                        
                    return result
            except:
                pass
            
            return {"status": "ERROR", "logs": logs}
            
        except Exception as e:
            if container:
                try: container.kill(); container.remove()
                except: pass
            return {"status": "ERROR", "logs": str(e)}
