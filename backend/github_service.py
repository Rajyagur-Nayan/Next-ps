import git
import requests
import re
import os
from git import GitCommandError
from backend.utils.file_utils import FileUtils

class GithubService:
    @staticmethod
    def secure_clone_repo(repo_url: str, username: str, token: str, workspace_path: str) -> dict:
        """
        Clones a repository securely using an injected token.
        """
        try:
            if not repo_url.startswith("https://"):
                 return {"status": "error", "message": "Repository URL must start with https://"}
            
            clean_url = repo_url.replace("https://", "")
            
            if username and token:
                auth_url = f"https://{username}:{token}@{clean_url}"
            elif token:
                 auth_url = f"https://{token}@{clean_url}"
            else:
                 auth_url = repo_url
            
            repo_name = clean_url.split("/")[-1].replace(".git", "")
            clone_path = os.path.join(workspace_path, repo_name)
            
            FileUtils.safe_delete_folder(clone_path)
            
            try:
                git.Repo.clone_from(auth_url, clone_path)
            except GitCommandError as e:
                error_msg = str(e).replace(token, "***TOKEN***")
                return {"status": "error", "message": f"Git Error: {error_msg}"}
            except Exception as e:
                 return {"status": "error", "message": f"Unexpected error: {str(e)}"}

            return {
                "status": "success",
                "message": "Repository cloned successfully",
                "repo_path": clone_path,
                "workspace": workspace_path
            }

        except Exception as e:
             return {"status": "error", "message": f"System error: {str(e)}"}

    @staticmethod
    def create_fix_branch(repo_path: str, team_name: str, leader_name: str) -> str:
        """
        Creates a new branch with strict format: TEAMNAME_LEADERNAME_AI_Fix
        """
        # Strict checking/cleaning
        def clean(s):
            return re.sub(r'[^A-Z0-9_]', '', s.upper().replace(' ', '_'))
            
        t_clean = clean(team_name)
        l_clean = clean(leader_name)
        
        branch_name = f"{t_clean}_{l_clean}_AI_Fix"
        
        repo = git.Repo(repo_path)
        try:
            current = repo.active_branch
            # Check if exists
            if branch_name in repo.heads:
                repo.heads[branch_name].checkout()
            else:
                repo.create_head(branch_name).checkout()
                
            return branch_name
        except Exception as e:
            print(f"Branch error: {e}")
            return branch_name # Fallback or error?

    @staticmethod
    def commit_and_push(repo_path: str, message: str, branch_name: str, token: str) -> dict:
        try:
            repo = git.Repo(repo_path)
            
            # Configure user
            with repo.config_writer() as cw:
                cw.set_value("user", "name", "AI Agent")
                cw.set_value("user", "email", "ai-agent@hackathon.com")

            if message:
                repo.git.add('.')
                try:
                    repo.git.commit('-m', message)
                except git.exc.GitCommandError as e:
                    if "nothing to commit" in str(e):
                        # If just verifying push or empty, proceed?
                        pass 
                    else:
                        raise e
            
            # Push securely
            origin = repo.remotes.origin
            url = origin.url
            if "https://" in url and "@" not in url:
                clean = url.replace("https://", "")
                auth_url = f"https://{token}@{clean}"
                repo.git.push(auth_url, f"HEAD:{branch_name}")
            else:
                repo.git.push('origin', f"HEAD:{branch_name}")
                
            return {"status": "success"}
        except Exception as e:
            msg = str(e).replace(token, "***TOKEN***")
            return {"status": "error", "message": msg}

    @staticmethod
    def create_pr(repo_url: str, branch_name: str, token: str, title: str, body: str) -> dict:
        """
        Creates a Pull Request using GitHub API.
        """
        try:
            clean_url = repo_url.replace("https://github.com/", "").replace(".git", "")
            owner, repo = clean_url.split("/")
            
            api_url = f"https://api.github.com/repos/{owner}/{repo}/pulls"
            
            headers = {
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28"
            }
            
            data = {
                "title": title,
                "body": body,
                "head": branch_name,
                "base": "main" # Assuming main, ideally detecting default branch
            }
            
            resp = requests.post(api_url, headers=headers, json=data)
            
            if resp.status_code == 201:
                return {"status": "success", "url": resp.json().get("html_url")}
            elif resp.status_code == 422:
                # Often means PR already exists
                return {"status": "warning", "message": "PR might already exist"}
            else:
                return {"status": "error", "message": f"GitHub API {resp.status_code}: {resp.text}"}
                
        except Exception as e:
            return {"status": "error", "message": str(e)}
