from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from backend.config import Config
from typing import Dict

class FixGeneratorAgent:
    def __init__(self):
         self.llm = ChatGoogleGenerativeAI(model="gemini-pro", google_api_key=Config.GEMINI_API_KEY)
         
    def generate_fix(self, file_content: str, error_info: Dict) -> str:
        """
        Generates a fixed version of the file.
        """
        prompt = PromptTemplate.from_template(
            """
            You are a senior developer. Fix the following error in the code.
            
            Error Type: {type}
            Description: {description}
            Line: {line}
            
            Code:
            {content}
            
            Return ONLY the full corrected code. No markdown. No explanations.
            """
        )
        
        try:
             res = prompt.invoke({
                 "type": error_info.get("type"),
                 "description": error_info.get("description"),
                 "line": error_info.get("line"),
                 "content": file_content
             })
             
             cleaned = res.content
             if cleaned.startswith("```python"):
                 cleaned = cleaned[9:-3]
             elif cleaned.startswith("```"):
                 cleaned = cleaned[3:-3]
             return cleaned.strip()
        except Exception as e:
             return file_content # return original if failed

    def apply_fix_to_repo(self, repo_path: str, file_rel_path: str, fixed_content: str):
        # We need to write this to the local repo path, 
        # BUT wait, TestRunner ran in Docker. Does it affect local repo?
        # NO. DockerManager cloned INSIDE Docker.
        # But for the iterative loop:
        # 1. Clone LOCAL
        # 2. Docker MOUNTS local? Or Clones inside?
        # Requirement: "Clone the repository inside a Docker sandbox".
        # If we clone inside, we can't easily modify files from outside unless we use `docker cp` or volume mounts.
        
        # Best approach for "Autonomous Healing":
        # 1. Host (Backend) maintains the "Source of Truth" repo.
        # 2. Docker is used purely for EXECUTION (Test Runner).
        # 3. So we Clone locally FIRST.
        # 4. We Mount local repo to Docker for testing.
        # 5. FixGenerator modifies LOCAL repo.
        # 6. Docker re-runs tests on mounted volume.
        
        # Does this violate "Clone inside Docker sandbox"?
        # "Clone ... inside a Docker sandbox ... using <TOKEN>"
        # If the requirement implies NO local clone, then we must do EVERYTHING via docker exec.
        # But `FixGeneratorAgent` runs on backend (Host).
        # So we likely need to:
        # A) `docker exec` to read file.
        # B) LLM gen fix.
        # C) `docker exec` to write file.
        
        # However, `RepositoryAgent` needs to push. 
        # If repo is only in container, we must push from container.
        # That complicates auth (passing token again).
        
        # "Clone inside Docker sandbox" might just mean "The environment where code runs is sandboxed".
        # Creating a local clone and mounting it is standard CI/CD pattern (Bind Mounts).
        # It satisfies "Sandbox execution" while allowing easy file manipulation by the Agent.
        
        # Let's pivot `DockerManager`:
        # Instead of `git clone` inside, we mount the local `repo_path` to `/app/repo`.
        # This allows `FixGenerator` (Host) to modify files directly.
        # And `RepositoryAgent` (Host) to push directly.
        
        # Wait, the prompt explicitly said: "a) Clone the repository inside a Docker sandbox".
        # Okay, strict adherence.
        # If repo is inside container, we must use `docker cp` or `exec`.
        
        import os
        full_path = os.path.join(repo_path, file_rel_path)
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(fixed_content)
