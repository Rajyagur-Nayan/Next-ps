from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import threading
import time
import json
import os
from datetime import datetime
from backend.langgraph_flow import app as autonomous_app

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class AutonomousRunRequest(BaseModel):
    repo_url: str
    team_name: str
    leader_name: str
    github_token: str

# Session State for Dashboard
session_state = {
    "status": "IDLE",
    "logs": [],
    "repo_url": "",
    "branch_name": "",
    "total_failures": 0,
    "fixes_applied": [],
    "iteration": 0,
    "max_iterations": 5,
    "final_status": "PENDING",
    "time_taken": "0s",
    "score": 100,
    "start_time": 0
}

def run_autonomous_agent(req: AutonomousRunRequest):
    global session_state
    session_state["status"] = "RUNNING"
    session_state["logs"] = []
    session_state["repo_url"] = req.repo_url
    session_state["fixes_applied"] = []
    session_state["iteration"] = 0
    session_state["final_status"] = "PENDING"
    session_state["start_time"] = time.time()
    
    initial_state = {
        "repo_url": req.repo_url,
        "team_name": req.team_name,
        "leader_name": req.leader_name,
        "token": req.github_token,
        "workspace": "",
        "repo_path": "",
        "branch_name": "",
        "iteration": 0,
        "max_iterations": 5,
        "test_status": "PENDING",
        "logs": [],
        "fixes_applied": [],
        "current_error": {}
    }
    
    try:
        # Run LangGraph
        final_state = autonomous_app.invoke(initial_state)
        
        # Calculate Stats
        end_time = time.time()
        duration = end_time - session_state["start_time"]
        minutes = int(duration // 60)
        seconds = int(duration % 60)
        time_str = f"{minutes}m {seconds}s"
        
        # Score Logic
        base_score = 100
        if duration < 300: # Bonus if < 5 mins
            base_score += 10
        
        # Penalty for extra commits (iterations)
        commits_made = len(final_state.get("fixes_applied", []))
        if commits_made > 20: # Example logic from prompt "penalty per commit over 20"
             base_score -= (commits_made - 20) * 2
        
        status = "PASSED" if final_state.get("test_status") == "PASSED" else "FAILED"
        
        # strict results.json format
        results = {
            "repo_url": req.repo_url,
            "branch": final_state.get("branch_name", "unknown"),
            "total_failures": len(final_state.get("fixes_applied", [])), # Approximation
            "fixes_applied": len(final_state.get("fixes_applied", [])),
            "iterations_used": final_state.get("iteration", 0),
            "max_iterations": 5,
            "status": status,
            "time_taken": time_str,
            "score": base_score,
            "fixes": final_state.get("fixes_applied", [])
        }
        
        # Update Session State
        session_state["branch_name"] = results["branch"]
        session_state["total_failures"] = results["total_failures"]
        session_state["fixes_applied"] = results["fixes"]
        session_state["iteration"] = results["iterations_used"]
        session_state["final_status"] = status
        session_state["time_taken"] = time_str
        session_state["score"] = base_score
        session_state["logs"] = final_state.get("logs", [])
        session_state["status"] = "COMPLETED"
        
        # Save results.json
        if final_state.get("workspace"):
             path = os.path.join(final_state["workspace"], "results.json")
             with open(path, 'w') as f:
                 json.dump(results, f, indent=2)
                 
    except Exception as e:
        session_state["status"] = "ERROR"
        session_state["logs"].append(f"Critical System Error: {str(e)}")

@app.get("/status")
async def get_status():
    return session_state

@app.post("/start-autonomous-run")
async def start_autonomous_run(req: AutonomousRunRequest):
    if session_state["status"] == "RUNNING":
        raise HTTPException(status_code=400, detail="Agent is already running")
        
    thread = threading.Thread(target=run_autonomous_agent, args=(req,))
    thread.start()
    return {"message": "Autonomous Agent Started"}
