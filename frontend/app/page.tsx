"use client";

import React, { useState, useEffect, useRef } from "react";
import axios from "axios";
import {
  Activity,
  Shield,
  Zap,
  GitBranch,
  Terminal,
  CheckCircle,
  XCircle,
  Clock,
  Award,
  Hammer,
  AlertTriangle,
  Loader2,
} from "lucide-react";

const API_URL = "http://localhost:8000";

// --- Components ---

const StatusBadge = ({ status }: { status: string }) => {
  const styles = {
    PASSED: "bg-green-900/50 text-green-400 border-green-700",
    FAILED: "bg-red-900/50 text-red-400 border-red-700",
    PENDING: "bg-yellow-900/50 text-yellow-400 border-yellow-700",
    RUNNING: "bg-blue-900/50 text-blue-400 border-blue-700 animate-pulse",
  };
  const s = status as keyof typeof styles;
  return (
    <span
      className={`px-3 py-1 rounded-full text-xs font-bold border ${styles[s] || styles.PENDING}`}
    >
      {status}
    </span>
  );
};

export default function Dashboard() {
  // State
  const [formData, setFormData] = useState({
    repo_url: "",
    team_name: "",
    leader_name: "",
    github_token: "",
  });

  const [status, setStatus] = useState<any>({
    status: "IDLE",
    logs: [],
    final_status: "PENDING",
    score: 100,
    time_taken: "0s",
    iteration: 0,
    max_iterations: 5,
    fixes_applied: [],
    total_failures: 0,
    branch_name: "---",
  });

  const logsEndRef = useRef<HTMLDivElement>(null);

  // Polling
  useEffect(() => {
    const poll = async () => {
      try {
        const res = await axios.get(`${API_URL}/status`);
        setStatus(res.data);
      } catch (e) {
        console.error("Polling error", e);
      }
    };

    const interval = setInterval(poll, 2000);
    return () => clearInterval(interval);
  }, []);

  // Scroll logs
  useEffect(() => {
    logsEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [status.logs]);

  const handleRun = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await axios.post(`${API_URL}/start-autonomous-run`, formData);
    } catch (err) {
      alert("Failed to start agent. Check console.");
    }
  };

  const isRunning = status.status === "RUNNING";

  return (
    <div className="min-h-screen bg-[#0f172a] text-slate-200 font-sans selection:bg-blue-500/30">
      {/* Navbar */}
      <nav className="border-b border-slate-800 bg-[#1e293b]/50 backdrop-blur-md sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Shield className="w-8 h-8 text-emerald-400" />
            <h1 className="text-xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-emerald-400 to-cyan-400">
              RIFT 2026: Autonomous Healing Agent
            </h1>
          </div>
          <div className="flex items-center gap-4 text-sm text-slate-400">
            <span className="flex items-center gap-1">
              <Terminal size={14} /> v2.0.0 (Production)
            </span>
          </div>
        </div>
      </nav>

      <main className="max-w-7xl mx-auto px-6 py-8 grid grid-cols-1 lg:grid-cols-12 gap-8">
        {/* Left Column: Inputs & Score - Span 4 */}
        <div className="lg:col-span-4 space-y-6">
          {/* Input Panel */}
          <div className="bg-[#1e293b] rounded-xl border border-slate-700 shadow-xl overflow-hidden">
            <div className="p-4 border-b border-slate-700 bg-slate-800/50 flex items-center gap-2">
              <Activity className="text-blue-400" size={18} />
              <h2 className="font-semibold text-slate-100">Configuration</h2>
            </div>
            <div className="p-6">
              <form onSubmit={handleRun} className="space-y-4">
                <div>
                  <label className="text-xs font-mono text-slate-400 uppercase">
                    Repository URL
                  </label>
                  <input
                    className="w-full bg-slate-900 border border-slate-700 rounded-md p-2 text-sm focus:border-blue-500 outline-none transition-colors"
                    placeholder="https://github.com/owner/repo"
                    value={formData.repo_url}
                    onChange={(e) =>
                      setFormData({ ...formData, repo_url: e.target.value })
                    }
                    disabled={isRunning}
                    required
                  />
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="text-xs font-mono text-slate-400 uppercase">
                      Team Name
                    </label>
                    <input
                      className="w-full bg-slate-900 border border-slate-700 rounded-md p-2 text-sm focus:border-blue-500 outline-none"
                      placeholder="Team Alpha"
                      value={formData.team_name}
                      onChange={(e) =>
                        setFormData({ ...formData, team_name: e.target.value })
                      }
                      disabled={isRunning}
                      required
                    />
                  </div>
                  <div>
                    <label className="text-xs font-mono text-slate-400 uppercase">
                      Leader Name
                    </label>
                    <input
                      className="w-full bg-slate-900 border border-slate-700 rounded-md p-2 text-sm focus:border-blue-500 outline-none"
                      placeholder="John Doe"
                      value={formData.leader_name}
                      onChange={(e) =>
                        setFormData({
                          ...formData,
                          leader_name: e.target.value,
                        })
                      }
                      disabled={isRunning}
                      required
                    />
                  </div>
                </div>
                <div>
                  <label className="text-xs font-mono text-slate-400 uppercase">
                    GitHub Token (Secure)
                  </label>
                  <input
                    type="password"
                    className="w-full bg-slate-900 border border-slate-700 rounded-md p-2 text-sm focus:border-blue-500 outline-none"
                    placeholder="github_pat_..."
                    value={formData.github_token}
                    onChange={(e) =>
                      setFormData({ ...formData, github_token: e.target.value })
                    }
                    disabled={isRunning}
                    required
                  />
                </div>

                <button
                  type="submit"
                  disabled={isRunning}
                  className="w-full bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white font-bold py-3 rounded-lg shadow-lg flex justify-center items-center gap-2 transition-all disabled:opacity-50 disabled:cursor-not-allowed mt-4"
                >
                  {isRunning ? (
                    <Loader2 className="animate-spin" />
                  ) : (
                    <Zap size={18} fill="currentColor" />
                  )}
                  {isRunning ? "AGENT RUNNING..." : "RUN AGENT"}
                </button>
              </form>
            </div>
          </div>

          {/* Score Panel */}
          <div className="bg-[#1e293b] rounded-xl border border-slate-700 shadow-xl overflow-hidden relative">
            <div className="absolute top-0 right-0 p-4 opacity-10">
              <Award size={100} />
            </div>
            <div className="p-6">
              <h3 className="text-slate-400 text-xs font-mono uppercase mb-1">
                Final Score
              </h3>
              <div className="flex items-baseline gap-2">
                <span className="text-5xl font-black text-white">
                  {status.score}
                </span>
                <span className="text-slate-500">/ 100</span>
              </div>

              <div className="mt-6 space-y-3">
                <div className="flex justify-between text-sm">
                  <span className="text-slate-400">Base Score</span>
                  <span className="font-mono">100</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-slate-400">Time Bonus ({"<"} 5m)</span>
                  <span className="font-mono text-emerald-400">
                    {parseInt(status.time_taken) < 5 ? "+10" : "0"}
                  </span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-slate-400">
                    Commit Penalty ({">"} 20)
                  </span>
                  <span className="font-mono text-red-400">0</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Right Column: Summaries & Logs - Span 8 */}
        <div className="lg:col-span-8 space-y-6">
          {/* Run Summary Grid */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="bg-[#1e293b] p-4 rounded-xl border border-slate-700 flex flex-col justify-between">
              <div className="flex items-center gap-2 text-slate-400 mb-2">
                <GitBranch size={16} />{" "}
                <span className="text-xs uppercase">Branch</span>
              </div>
              <div
                className="font-mono text-xs text-blue-300 break-all"
                title={status.branch_name}
              >
                {status.branch_name.length > 20
                  ? status.branch_name.substring(0, 18) + "..."
                  : status.branch_name}
              </div>
            </div>

            <div className="bg-[#1e293b] p-4 rounded-xl border border-slate-700 flex flex-col justify-between">
              <div className="flex items-center gap-2 text-slate-400 mb-2">
                <AlertTriangle size={16} />{" "}
                <span className="text-xs uppercase">Failures</span>
              </div>
              <div className="text-2xl font-bold text-white">
                {status.total_failures}
              </div>
            </div>

            <div className="bg-[#1e293b] p-4 rounded-xl border border-slate-700 flex flex-col justify-between">
              <div className="flex items-center gap-2 text-slate-400 mb-2">
                <Hammer size={16} />{" "}
                <span className="text-xs uppercase">Fixes</span>
              </div>
              <div className="text-2xl font-bold text-white">
                {status.fixes_applied.length}
              </div>
            </div>

            <div className="bg-[#1e293b] p-4 rounded-xl border border-slate-700 flex flex-col justify-between">
              <div className="flex items-center gap-2 text-slate-400 mb-2">
                <Clock size={16} />{" "}
                <span className="text-xs uppercase">Time</span>
              </div>
              <div className="text-2xl font-bold text-white">
                {status.time_taken}
              </div>
            </div>
          </div>

          {/* Timeline & Status */}
          <div className="bg-[#1e293b] rounded-xl border border-slate-700 shadow-xl overflow-hidden p-6">
            <div className="flex justify-between items-center mb-6">
              <h3 className="font-semibold text-slate-100 flex items-center gap-2">
                <Activity className="text-emerald-400" size={20} /> Executing
                Workflow
              </h3>
              <StatusBadge status={status.final_status} />
            </div>

            {/* Visual Progress/Timeline */}
            <div className="relative pt-2 pb-6">
              <div className="h-2 bg-slate-800 rounded-full overflow-hidden">
                <div
                  className="h-full bg-blue-500 transition-all duration-500 ease-out"
                  style={{
                    width: `${(status.iteration / status.max_iterations) * 100}%`,
                  }}
                />
              </div>
              <div className="flex justify-between mt-2 text-xs text-slate-500 font-mono">
                <span>START</span>
                <span>
                  ITERATION {status.iteration} / {status.max_iterations}
                </span>
                <span>FINISH</span>
              </div>
            </div>
          </div>

          {/* Fixes Table */}
          <div className="bg-[#1e293b] rounded-xl border border-slate-700 shadow-xl overflow-hidden">
            <div className="p-4 border-b border-slate-700 bg-slate-800/50">
              <h3 className="font-semibold text-slate-100">Fixes Applied</h3>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm text-slate-300">
                <thead className="bg-[#1e293b] text-slate-500 uppercase text-xs border-b border-slate-700">
                  <tr>
                    <th className="px-4 py-3 font-medium">Type</th>
                    <th className="px-4 py-3 font-medium">File</th>
                    <th className="px-4 py-3 font-medium">Line</th>
                    <th className="px-4 py-3 font-medium">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800">
                  {status.fixes_applied.length === 0 ? (
                    <tr>
                      <td
                        colSpan={4}
                        className="px-4 py-8 text-center text-slate-500"
                      >
                        No fixes applied yet.
                      </td>
                    </tr>
                  ) : (
                    status.fixes_applied.map((fix: any, i: number) => (
                      <tr
                        key={i}
                        className="hover:bg-slate-800/50 transition-colors"
                      >
                        <td className="px-4 py-3 font-mono text-xs">
                          <span className="px-2 py-0.5 rounded bg-purple-900/40 text-purple-400 border border-purple-800/50">
                            {fix.bug_type}
                          </span>
                        </td>
                        <td className="px-4 py-3 font-mono">{fix.file}</td>
                        <td className="px-4 py-3 font-mono text-slate-500">
                          {fix.line_number}
                        </td>
                        <td className="px-4 py-3">
                          {fix.status.includes("Fixed") ? (
                            <span className="flex items-center gap-1 text-emerald-400 text-xs font-bold">
                              <CheckCircle size={12} /> FIXED
                            </span>
                          ) : (
                            <span className="flex items-center gap-1 text-yellow-400 text-xs font-bold">
                              <Activity size={12} /> APPLIED
                            </span>
                          )}
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>

          {/* Logs Console */}
          <div className="bg-[#0f172a] rounded-xl border border-slate-700 shadow-xl overflow-hidden font-mono text-xs">
            <div className="p-2 bg-slate-800 border-b border-slate-700 text-slate-400 flex justify-between items-center px-4">
              <span>TERMINAL OUTPUT</span>
              <div className="flex gap-1.5">
                <div className="w-2.5 h-2.5 rounded-full bg-red-500/50"></div>
                <div className="w-2.5 h-2.5 rounded-full bg-yellow-500/50"></div>
                <div className="w-2.5 h-2.5 rounded-full bg-green-500/50"></div>
              </div>
            </div>
            <div className="h-64 overflow-y-auto p-4 space-y-1 text-slate-300">
              {status.logs.map((log: string, i: number) => (
                <div key={i} className="break-words">
                  <span className="text-slate-600 select-none mr-3 opacity-50">
                    $
                  </span>
                  {log}
                </div>
              ))}
              <div ref={logsEndRef} />
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
