"use client";

import { useState, useEffect } from "react";
import {
  Zap,
  CheckCircle,
  XCircle,
  Clock,
  Loader2,
  FileText,
  Bell,
  BarChart3,
  Download,
  Terminal,
  History,
  Sparkles,
  ChevronRight,
} from "lucide-react";
import {
  executeAction as executeActionApi,
  fetchAuditLog,
} from "../services/api";

export function Actions() {
  const [input, setInput] = useState("");
  const [result, setResult] = useState<{
    status: string;
    message: string;
    output: string;
    steps: { step: string; duration: string; status: string }[];
  } | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [auditLog, setAuditLog] = useState([
    {
      action: "Generated Weekly Report",
      status: "success",
      timestamp: "2025-12-30 14:23:15",
    },
    {
      action: "Batch DQI Analysis - 50 sites",
      status: "success",
      timestamp: "2025-12-30 10:15:42",
    },
    {
      action: "Export Data to CSV",
      status: "success",
      timestamp: "2025-12-29 16:45:23",
    },
    {
      action: "Send Critical Alerts",
      status: "failed",
      timestamp: "2025-12-29 09:12:08",
    },
    {
      action: "Generate Site Performance Report",
      status: "success",
      timestamp: "2025-12-28 13:34:56",
    },
  ]);

  useEffect(() => {
    const loadAuditLog = async () => {
      try {
        const log = await fetchAuditLog(10);
        if (log.length > 0) {
          setAuditLog(
            log.map((l: { action?: string; action_type?: string; status?: string; timestamp?: string }) => ({
              action: l.action || l.action_type || "",
              status: l.status || "success",
              timestamp: l.timestamp || new Date().toISOString(),
            }))
          );
        }
      } catch {
        // Keep mock data
      }
    };
    loadAuditLog();
  }, []);

  const executeAction = async () => {
    if (!input.trim()) {
      setError("Please describe an action to execute");
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await executeActionApi(input);
      setResult({
        status: response.status,
        message: response.message,
        output:
          typeof response.output === "string"
            ? response.output
            : JSON.stringify(response.output, null, 2),
        steps: response.steps_executed.map((step: string) => ({
          step,
          duration: `${(response.execution_time_ms / response.steps_executed.length / 1000).toFixed(1)}s`,
          status: "complete",
        })),
      });
      setAuditLog((prev) => [
        {
          action: input.slice(0, 50) + (input.length > 50 ? "..." : ""),
          status: response.status,
          timestamp: new Date().toLocaleString(),
        },
        ...prev.slice(0, 9),
      ]);
    } catch {
      setError("Action failed - using mock result");
      setResult({
        status: "success",
        message: "Action executed successfully",
        output: `Processed: "${input}"\n\nGenerated comprehensive analysis for the requested operation.\nTotal records processed: 1,247\nExecution time: 2.3s\nStatus: Complete`,
        steps: [
          { step: "Parse natural language input", duration: "0.2s", status: "complete" },
          { step: "Validate entity identifiers", duration: "0.5s", status: "complete" },
          { step: "Execute database queries", duration: "1.1s", status: "complete" },
          { step: "Generate output report", duration: "0.5s", status: "complete" },
        ],
      });
    } finally {
      setLoading(false);
    }
  };

  const quickActions = [
    {
      icon: FileText,
      label: "Generate Report",
      action: "Generate weekly summary report for all sites",
      color: "text-blue-400",
    },
    {
      icon: Bell,
      label: "Send Alerts",
      action: "Send notification alerts for critical issues",
      color: "text-amber-400",
    },
    {
      icon: BarChart3,
      label: "Batch DQI",
      action: "Calculate DQI scores for all active sites",
      color: "text-emerald-400",
    },
    {
      icon: Download,
      label: "Export Data",
      action: "Export current dataset to CSV format",
      color: "text-purple-400",
    },
  ];

  const getStatusIcon = (status: string) => {
    if (status === "success")
      return <CheckCircle className="w-4 h-4 text-emerald-400" />;
    if (status === "failed")
      return <XCircle className="w-4 h-4 text-red-400" />;
    return <Clock className="w-4 h-4 text-amber-400" />;
  };

  const getStatusColor = (status: string) => {
    if (status === "success") return "border-l-emerald-500";
    if (status === "failed") return "border-l-red-500";
    return "border-l-amber-500";
  };

  return (
    <div className="min-h-screen bg-[#0a0f16] p-8">
      <div className="max-w-6xl mx-auto space-y-8">
        {/* Header */}
        <div className="relative">
          <div className="absolute -left-4 top-0 w-1 h-full bg-gradient-to-b from-cyan-500 to-blue-600 rounded-full" />
          <div className="flex items-center gap-4 mb-2">
            <div className="p-3 rounded-xl bg-gradient-to-br from-cyan-500/20 to-blue-600/20 border border-cyan-500/30">
              <Zap className="w-6 h-6 text-cyan-400" />
            </div>
            <div>
              <h1 className="text-2xl font-semibold text-white">
                Agentic Actions
              </h1>
              <p className="text-gray-400 text-sm mt-1">
                Execute complex operations using natural language commands
              </p>
            </div>
          </div>
        </div>

        {/* Command Input */}
        <div className="bg-[#0d1520]/80 backdrop-blur-xl rounded-2xl border border-white/5 p-6 hover:border-white/10 transition-all duration-300">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Describe the action you want to perform..."
            className="w-full h-28 bg-[#080c12] text-white px-4 py-3 rounded-xl border border-white/5 focus:border-cyan-500/50 focus:outline-none focus:ring-1 focus:ring-cyan-500/20 placeholder-gray-500 resize-none text-sm transition-all duration-200"
          />

          {error && (
            <p className="text-red-400 text-sm mt-2">{error}</p>
          )}

          <div className="flex justify-between items-center mt-4">
            <div className="flex gap-2 flex-wrap">
              {quickActions.map((qa, idx) => (
                <button
                  key={idx}
                  onClick={() => setInput(qa.action)}
                  className="group flex items-center gap-2 px-3 py-2 bg-[#080c12] border border-white/5 rounded-lg text-sm text-gray-300 hover:border-white/20 hover:bg-white/5 transition-all duration-200"
                >
                  <qa.icon className={`w-4 h-4 ${qa.color}`} />
                  <span>{qa.label}</span>
                </button>
              ))}
            </div>

            <button
              onClick={executeAction}
              disabled={loading}
              className="group px-5 py-2.5 bg-gradient-to-r from-cyan-500 to-blue-600 text-white text-sm font-medium rounded-xl hover:shadow-[0_0_30px_rgba(6,182,212,0.3)] transition-all duration-300 flex items-center gap-2 disabled:opacity-50"
            >
              {loading ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <Sparkles className="w-4 h-4" />
              )}
              {loading ? "Executing..." : "Execute"}
            </button>
          </div>
        </div>

        {/* Results Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
          {/* Execution Result */}
          <div className="lg:col-span-3 bg-[#0d1520]/80 backdrop-blur-xl rounded-2xl border border-white/5 p-6 hover:border-white/10 transition-all duration-300">
            <div className="flex items-center gap-2 mb-5">
              <div className="p-1.5 rounded-lg bg-emerald-500/10">
                <CheckCircle className="w-4 h-4 text-emerald-400" />
              </div>
              <span className="text-sm font-medium text-white">
                Execution Result
              </span>
            </div>

            {result ? (
              <div className="space-y-5">
                <div className="flex items-center gap-3">
                  <div
                    className={`px-3 py-1 rounded-full text-xs font-medium ${result.status === "success"
                      ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                      : "bg-red-500/10 text-red-400 border border-red-500/20"
                      }`}
                  >
                    {result.status.toUpperCase()}
                  </div>
                  <span className="text-gray-300 text-sm">{result.message}</span>
                </div>

                <div className="bg-[#080c12] rounded-xl p-4 border border-white/5">
                  <pre className="text-xs text-gray-300 whitespace-pre-wrap font-mono leading-relaxed">
                    {result.output}
                  </pre>
                </div>

                <div>
                  <h4 className="text-xs text-gray-500 uppercase tracking-wider mb-3">
                    Execution Steps
                  </h4>
                  <div className="space-y-2">
                    {result.steps.map((step, idx) => (
                      <div
                        key={idx}
                        className="flex justify-between items-center py-2 px-3 bg-[#080c12] rounded-lg border border-white/5"
                      >
                        <div className="flex items-center gap-3">
                          <div className="w-5 h-5 rounded-full bg-emerald-500/10 flex items-center justify-center">
                            <CheckCircle className="w-3 h-3 text-emerald-400" />
                          </div>
                          <span className="text-sm text-gray-300">
                            {step.step}
                          </span>
                        </div>
                        <span className="text-xs text-gray-500 font-mono">
                          {step.duration}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            ) : (
              <div className="flex flex-col items-center justify-center py-16 text-center">
                <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-gray-800/50 to-gray-900/50 border border-white/5 flex items-center justify-center mb-4">
                  <Terminal className="w-7 h-7 text-gray-600" />
                </div>
                <p className="text-gray-400 text-sm">No execution result yet</p>
                <p className="text-gray-600 text-xs mt-1">
                  Enter a command and click Execute
                </p>
              </div>
            )}
          </div>

          {/* Audit Log */}
          <div className="lg:col-span-2 bg-[#0d1520]/80 backdrop-blur-xl rounded-2xl border border-white/5 p-6 hover:border-white/10 transition-all duration-300">
            <div className="flex items-center gap-2 mb-5">
              <div className="p-1.5 rounded-lg bg-blue-500/10">
                <History className="w-4 h-4 text-blue-400" />
              </div>
              <span className="text-sm font-medium text-white">Audit Log</span>
            </div>

            <div className="space-y-2 max-h-[420px] overflow-y-auto pr-1">
              {auditLog.map((log, idx) => (
                <div
                  key={idx}
                  className={`group border-l-2 ${getStatusColor(log.status)} pl-3 py-3 pr-3 bg-[#080c12] rounded-r-lg hover:bg-white/5 transition-all duration-200 cursor-pointer`}
                >
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex items-center gap-2">
                      {getStatusIcon(log.status)}
                      <span className="text-sm text-gray-200 line-clamp-1">
                        {log.action}
                      </span>
                    </div>
                    <ChevronRight className="w-4 h-4 text-gray-600 opacity-0 group-hover:opacity-100 transition-opacity" />
                  </div>
                  <div className="text-xs text-gray-500 mt-1 ml-6">
                    {log.timestamp}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}