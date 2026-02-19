from typing import Dict
from backend.docker_manager import DockerManager

class TestRunnerAgent:
    def __init__(self):
        self.docker_manager = DockerManager()
        
    def run_tests(self, repo_url: str, branch_name: str, token: str) -> Dict:
        """
        Runs tests using Docker.
        """
        # We don't need repo_path here since DockerManager handles cloning inside the container
        # But we might need a local path if we were mounting.
        # DockerManager.run_tests_in_sandbox signature: repo_path, repo_url, branch_name, token
        # Let's adjust usage to match DockerManager.
        
        # Actually in DockerManager we implemented:
        # run_tests_in_sandbox(repo_path, repo_url, branch_name, token)
        # But for "Sandbox Clone", we only need URL, Branch, Token.
        # repo_path was unused in DockerManager implementation for cloning-inside strategy.
        
        results = self.docker_manager.run_tests_in_sandbox(None, repo_url, branch_name, token)
        return results
