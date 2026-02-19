from langgraph.graph import StateGraph, END
from typing import TypedDict, List, Dict
import os
import shutil
from backend.config import Config
from backend.utils.file_utils import FileUtils, read_file_content
from backend.github_service import GithubService
from backend.agents.test_runner_agent import TestRunnerAgent
from backend.agents.bug_analyzer_agent import BugAnalyzerAgent
from backend.agents.fix_generator_agent import FixGeneratorAgent

# State Definition
class AgentState(TypedDict):
    repo_url: str
    team_name: str
    leader_name: str
    token: str
    workspace: str
    repo_path: str
    branch_name: str
    iteration: int
    max_iterations: int
    test_status: str # PASSED / FAILED / ERROR
    logs: List[str] # Rolling logs
    fixes_applied: List[Dict] # History of fixes
    current_error: Dict # Analysis result

# Agents
github_service = GithubService()
test_runner = TestRunnerAgent()
bug_analyzer = BugAnalyzerAgent()
fix_generator = FixGeneratorAgent()

# Nodes

def clone_node(state: AgentState):
    # 1. Create Workspace
    workspace = FileUtils.create_workspace()
    state["workspace"] = workspace
    
    # 2. Clone
    res = github_service.secure_clone_repo(state["repo_url"], "", state["token"], workspace)
    if res["status"] == "error":
        state["logs"].append(f"Clone Failed: {res['message']}")
        state["test_status"] = "ERROR"
        return state
        
    state["repo_path"] = res["repo_path"]
    state["logs"].append(f"Cloned repository to {state['repo_path']}")
    
    # 3. Create Branch
    branch = github_service.create_fix_branch(state["repo_path"], state["team_name"], state["leader_name"])
    state["branch_name"] = branch
    state["logs"].append(f"Created branch: {branch}")
    
    # 4. Push Branch IMMEDIATELY to ensure Docker can see it
    # We push an empty commit or just the branch ref?
    # Trying to push the branch as is (pointing to current HEAD).
    push_res = github_service.commit_and_push(state["repo_path"], None, branch, state["token"]) # Message None = just push
    if push_res["status"] == "error":
        state["logs"].append(f"Initial Push Failed: {push_res['message']}")
    else:
        state["logs"].append(f"Synced branch {branch} to remote for Sandbox.")

    return state

def test_node(state: AgentState):
    state["logs"].append(f"Running tests (Iteration {state['iteration'] + 1}/{state['max_iterations']})...")
    
    # Docker Execution
    # DockerManager will clone from REMOTE. 
    # Because we pushed in clone_node (and commit_node), remote has latest code.
    res = test_runner.run_tests(state["repo_url"], state["branch_name"], state["token"])
    
    state["test_status"] = res["status"]
    state["logs"].append(f"Test Result: {res['status']}")
    
    if res["status"] == "FAILED":
        state["current_error"] = {"raw_logs": res["logs"]}
        
    return state

def analyze_node(state: AgentState):
    state["logs"].append("Analyzing failure logs...")
    # Analyze raw logs
    logs = state["current_error"].get("raw_logs", "")
    analysis = bug_analyzer.analyze_logs(logs)
    state["current_error"].update(analysis)
    state["logs"].append(f"Detected {analysis.get('type')} error in {analysis.get('file')} line {analysis.get('line')}")
    return state

def fix_node(state: AgentState):
    err = state["current_error"]
    file_rel = err.get("file")
    
    full_path = os.path.join(state["repo_path"], file_rel)
    if not os.path.exists(full_path):
         state["logs"].append(f"File {file_rel} not found in workspace. Trying best guess...")
         # Fallback logic could go here
         state["iteration"] += 1
         return state
         
    content = read_file_content(full_path)
    fixed_content = fix_generator.generate_fix(content, err)
    
    if fixed_content == content:
        state["logs"].append("LLM could not generate a unique fix.")
    else:
        # Apply fix LOCALLY
        fix_generator.apply_fix_to_repo(state["repo_path"], file_rel, fixed_content)
        
        fix_record = {
            "file": file_rel,
            "bug_type": err.get("type"),
            "line_number": err.get("line"),
            "commit_message": f"[AI-AGENT] Fix {err.get('type')} error in {file_rel} line {err.get('line')}",
            "status": "Applied" 
        }
        state["fixes_applied"].append(fix_record)
        state["logs"].append(f"Applied fix locally to {file_rel}")
        
    return state

def commit_node(state: AgentState):
    if not state["fixes_applied"]:
        state["iteration"] += 1
        return state
        
    last_fix = state["fixes_applied"][-1]
    msg = last_fix["commit_message"]
    
    # Push changes to Remote so Docker can pull them next test_node run
    res = github_service.commit_and_push(state["repo_path"], msg, state["branch_name"], state["token"])
    
    if res["status"] == "success":
        last_fix["status"] = "Fixed"
        state["logs"].append("Committed and Synced changes to Remote Sandbox.")
    else:
        last_fix["status"] = "Failed Commit"
        state["logs"].append(f"Commit/Push failed: {res['message']}")
        
    state["iteration"] += 1
    return state

def pr_node(state: AgentState):
    state["logs"].append("Creating Pull Request...")
    title = f"AI Fixes for {state['team_name']}"
    body = f"Autonomous fixes generated by RIFT Agent.\n\nStats:\n- Iterations: {state['iteration']}\n- Fixes: {len(state['fixes_applied'])}"
    
    # Only create PR if we actually did something or if passed?
    # RIFT requirement: "Create Pull Request automatically"
    res = github_service.create_pr(state["repo_url"], state["branch_name"], state["token"], title, body)
    
    if res["status"] == "success":
        state["logs"].append(f"PR Created: {res['url']}")
    else:
        state["logs"].append(f"PR Creation Note: {res.get('message')}")
        
    return state

# Conditional Logic
def check_retry(state: AgentState):
    if state["test_status"] == "PASSED":
        return "create_pr"
    
    if state["test_status"] == "ERROR":
        # Docker failed entirely? Stop?
        return "create_pr"
        
    if state["iteration"] >= state["max_iterations"]:
        return "create_pr"
        
    return "analyze"

# Graph
workflow = StateGraph(AgentState)

workflow.add_node("clone", clone_node)
workflow.add_node("test", test_node)
workflow.add_node("analyze", analyze_node)
workflow.add_node("fix", fix_node)
workflow.add_node("commit", commit_node)
workflow.add_node("create_pr", pr_node)

workflow.set_entry_point("clone")
workflow.add_edge("clone", "test")

workflow.add_conditional_edges(
    "test",
    check_retry,
    {
        "create_pr": "create_pr",
        "analyze": "analyze"
    }
)

workflow.add_edge("analyze", "fix")
workflow.add_edge("fix", "commit")
workflow.add_edge("commit", "test")
workflow.add_edge("create_pr", END)

app = workflow.compile()
