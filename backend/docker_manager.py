import docker
import os
import shutil
import time
from typing import Dict, Tuple

class DockerManager:
    def __init__(self):
        try:
            self.client = docker.from_env()
        except Exception as e:
            print(f"Docker Error: {e}")
            self.client = None

    def run_tests_in_sandbox(self, repo_path: str, repo_url: str, branch_name: str, token: str) -> Dict[str, str]:
        """
        Runs tests in a Docker container.
        """
        if not self.client:
            return {"status": "ERROR", "logs": "Docker not available. Please ensure Docker Desktop is running."}

        # Dynamic Language Support: Use image with both Python and Node
        # Image: nikolaik/python-nodejs:python3.9-nodejs20 (A standard image with both)
        # If not available locally, it will pull (might take time first run).
        # Fallback: python:3.9 and install node? Takes too long.
        # Let's use `nikolaik/python-nodejs:python3.9-nodejs20`
        image_name = "nikolaik/python-nodejs:python3.9-nodejs20"
        
        container = None
        try:
            clean_url = repo_url.replace("https://", "")
            if token:
                 auth_url = f"https://{token}@{clean_url}"
            else:
                 auth_url = repo_url
            
            # Script to detect and run
            # We clone, then check files.
            
            script = f"""
            git clone {auth_url} /app/repo && \
            cd /app/repo && \
            git checkout {branch_name} || git checkout -b {branch_name} && \
            if [ -f "requirements.txt" ]; then \
                echo "Detected Python Project" && \
                pip install -r requirements.txt && \
                (pytest > test_logs.txt 2>&1 || true); \
            elif [ -f "package.json" ]; then \
                echo "Detected Node.js Project" && \
                npm install && \
                (npm test > test_logs.txt 2>&1 || true); \
            else \
                echo "No standard test config found (requirements.txt or package.json)" > test_logs.txt; \
            fi && \
            cat test_logs.txt
            """
            
            # Need git installed. The nikolaik image usually has git.
            # Just to be safe, try apt-get update if git missing?
            # Or just run.
            
            container = self.client.containers.run(
                image_name,
                command=f"bash -c '{script}'",
                detach=True,
                remove=False
            )
            
            exit_code = container.wait()
            logs = container.logs().decode("utf-8")
            
            container.remove()
            
            status = "PASSED"
            if "failed" in logs.lower() or "error" in logs.lower():
                 if " 1 failed" in logs or " errors" in logs or "failing" in logs:
                     status = "FAILED"
            
            safe_logs = logs.replace(token, "***TOKEN***")
            
            return {"status": status, "logs": safe_logs}
            
        except Exception as e:
            if container:
                try: 
                    container.kill() 
                    container.remove()
                except: pass
            
            return {"status": "ERROR", "logs": f"Sandbox Error: {str(e)}"}
