"use client";

import React from "react"

import { useState, useRef, useEffect } from "react";
import {
    Send,
    Loader2,
    Brain,
    Zap,
    Code,
    Clock,
    MessageSquare,
    Sparkles,
    ChevronDown,
    CheckCircle2,
    XCircle,
    Table,
} from "lucide-react";
import ReactMarkdown from "react-markdown";
import {
    executeQuery,
    executeNexusQuery,
    type QueryResponse,
    type NexusQueryResponse,
} from "../services/api";

type QueryMode = "planning" | "fast";

interface Message {
    id: string;
    type: "user" | "assistant";
    content: string;
    mode: QueryMode;
    timestamp: Date;
    metadata?: {
        sql?: string;
        timing?: Record<string, number>;
        success?: boolean;
        error?: string;
        executionResult?: {
            data?: Record<string, unknown>[];
            columns?: string[];
        };
    };
}

export function Chat() {
    const [mode, setMode] = useState<QueryMode>("fast");
    const [input, setInput] = useState("");
    const [messages, setMessages] = useState<Message[]>([]);
    const [loading, setLoading] = useState(false);
    const [sqlExpanded, setSqlExpanded] = useState<Record<string, boolean>>({});
    const messagesEndRef = useRef<HTMLDivElement>(null);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    const exampleQueries = [
        { icon: Table, text: "How many studies are in the database?" },
        { icon: Sparkles, text: "What is the average DQI score across all sites?" },
        { icon: MessageSquare, text: "Which sites have critical alerts?" },
        { icon: Code, text: "Show enrollment status by region" },
    ];

    const handleSend = async () => {
        if (!input.trim() || loading) return;

        const userMessage: Message = {
            id: Date.now().toString(),
            type: "user",
            content: input,
            mode,
            timestamp: new Date(),
        };

        setMessages((prev) => [...prev, userMessage]);
        setInput("");
        setLoading(true);

        try {
            let response: Message;

            if (mode === "fast") {
                const result: NexusQueryResponse = await executeNexusQuery(input);

                let mainContent = "";
                if (
                    result.execution_result?.data &&
                    result.execution_result.data.length > 0
                ) {
                    const data = result.execution_result.data;
                    const columns =
                        result.execution_result.columns || Object.keys(data[0]);

                    let table = "| " + columns.join(" | ") + " |\n";
                    table += "| " + columns.map(() => "---").join(" | ") + " |\n";
                    data.slice(0, 20).forEach((row: Record<string, unknown>) => {
                        const values = columns.map((col: string) =>
                            String(row[col] ?? "")
                        );
                        table += "| " + values.join(" | ") + " |\n";
                    });
                    if (data.length > 20) {
                        table += `\n*Showing 20 of ${data.length} rows*`;
                    }
                    mainContent = `**Query Results (${data.length} rows):**\n\n${table}`;
                } else if (result.explanation) {
                    mainContent = result.explanation;
                } else {
                    mainContent = "Query executed successfully. No results returned.";
                }

                response = {
                    id: (Date.now() + 1).toString(),
                    type: "assistant",
                    content: mainContent,
                    mode: "fast",
                    timestamp: new Date(),
                    metadata: {
                        sql: result.sql,
                        timing: result.metrics,
                        success: result.success,
                        error: result.error,
                        executionResult: result.execution_result,
                    },
                };
            } else {
                const result: QueryResponse = await executeQuery(input);
                response = {
                    id: (Date.now() + 1).toString(),
                    type: "assistant",
                    content: result.answer,
                    mode: "planning",
                    timestamp: new Date(),
                    metadata: {
                        timing: result.timing,
                        success: result.success,
                    },
                };
            }

            setMessages((prev) => [...prev, response]);
        } catch (error: unknown) {
            const errorMessage: Message = {
                id: (Date.now() + 1).toString(),
                type: "assistant",
                content: `Error: ${error instanceof Error ? error.message : "Failed to process query"}`,
                mode,
                timestamp: new Date(),
                metadata: {
                    success: false,
                    error: error instanceof Error ? error.message : "Unknown error",
                },
            };
            setMessages((prev) => [...prev, errorMessage]);
        } finally {
            setLoading(false);
        }
    };

    const handleKeyPress = (e: React.KeyboardEvent) => {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            handleSend();
        }
    };

    const toggleSql = (id: string) => {
        setSqlExpanded((prev) => ({ ...prev, [id]: !prev[id] }));
    };

    const formatTime = (date: Date) => {
        return date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
    };

    return (
        <div className="min-h-screen bg-[#0a0f18] text-white p-6">
            <div className="w-full flex flex-col h-[calc(100vh-48px)]">
                {/* Header */}
                <div className="mb-6">
                    <div className="flex items-start justify-between gap-4">
                        <div className="flex items-center gap-4">
                            <div className="relative">
                                <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-violet-500 to-purple-600 flex items-center justify-center">
                                    <MessageSquare className="w-6 h-6 text-white" />
                                </div>
                                <div className="absolute -bottom-1 -right-1 w-4 h-4 rounded-full bg-emerald-500 border-2 border-[#0a0f18]" />
                            </div>
                            <div>
                                <h1 className="text-2xl font-bold text-white">
                                    AI Query Assistant
                                </h1>
                                <p className="text-gray-400 text-sm">
                                    Ask questions about your clinical trial data
                                </p>
                            </div>
                        </div>

                        {/* Mode Toggle */}
                        <div className="flex items-center gap-2 p-1 bg-[#0d1520] rounded-xl border border-white/5 ml-auto mr-4">
                            <button
                                type="button"
                                onClick={() => setMode("planning")}
                                className={`flex items-center gap-2 px-4 py-2.5 rounded-lg text-sm font-medium transition-all ${mode === "planning"
                                    ? "bg-gradient-to-r from-blue-600 to-blue-500 text-white shadow-lg shadow-blue-500/25"
                                    : "text-gray-400 hover:text-white hover:bg-white/5"
                                    }`}
                            >
                                <Brain className="w-4 h-4" />
                                <span>Planning</span>
                            </button>
                            <button
                                type="button"
                                onClick={() => setMode("fast")}
                                className={`flex items-center gap-2 px-4 py-2.5 rounded-lg text-sm font-medium transition-all ${mode === "fast"
                                    ? "bg-gradient-to-r from-amber-500 to-orange-500 text-white shadow-lg shadow-orange-500/25"
                                    : "text-gray-400 hover:text-white hover:bg-white/5"
                                    }`}
                            >
                                <Zap className="w-4 h-4" />
                                <span>Fast</span>
                            </button>
                        </div>
                    </div>

                    {/* Mode Description */}
                    <div
                        className={`mt-4 flex items-center gap-3 px-4 py-3 rounded-xl text-sm ${mode === "planning"
                            ? "bg-blue-500/10 border border-blue-500/20"
                            : "bg-amber-500/10 border border-amber-500/20"
                            }`}
                    >
                        {mode === "planning" ? (
                            <>
                                <Brain
                                    className={`w-5 h-5 ${mode === "planning" ? "text-blue-400" : "text-amber-400"}`}
                                />
                                <span className="text-gray-300">
                                    <span
                                        className={`font-semibold ${mode === "planning" ? "text-blue-400" : "text-amber-400"}`}
                                    >
                                        Planning Mode:
                                    </span>{" "}
                                    Uses SAGE-CODE with graph reasoning for detailed analysis
                                </span>
                            </>
                        ) : (
                            <>
                                <Zap className="w-5 h-5 text-amber-400" />
                                <span className="text-gray-300">
                                    <span className="font-semibold text-amber-400">
                                        Fast Mode:
                                    </span>{" "}
                                    Trials Text-to-SQL pipeline for quick SQL generation
                                </span>
                            </>
                        )}
                    </div>
                </div>

                {/* Chat Area */}
                <div className="flex-1 overflow-y-auto rounded-2xl bg-[#0d1520]/50 border border-white/5 p-4">
                    {messages.length === 0 ? (
                        <div className="h-full flex flex-col items-center justify-center text-center px-4">
                            <div className="relative mb-6">
                                <div className="w-20 h-20 rounded-2xl bg-gradient-to-br from-violet-500/20 to-purple-600/20 flex items-center justify-center">
                                    <Sparkles className="w-10 h-10 text-violet-400" />
                                </div>
                                <div className="absolute inset-0 rounded-2xl bg-violet-500/20 blur-xl" />
                            </div>
                            <h3 className="text-lg font-medium text-white mb-2">
                                Start a conversation
                            </h3>
                            <p className="text-gray-500 text-sm mb-8 max-w-md">
                                Ask questions about your clinical trial data using natural
                                language
                            </p>

                            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 w-full max-w-xl">
                                {exampleQueries.map((query, idx) => (
                                    <button
                                        type="button"
                                        key={idx}
                                        onClick={() => setInput(query.text)}
                                        className="group flex items-center gap-3 px-4 py-3 bg-[#0d1520] border border-white/5 rounded-xl text-left text-sm text-gray-300 hover:border-violet-500/30 hover:bg-violet-500/5 transition-all"
                                    >
                                        <query.icon className="w-4 h-4 text-gray-500 group-hover:text-violet-400 transition-colors shrink-0" />
                                        <span className="line-clamp-1">{query.text}</span>
                                    </button>
                                ))}
                            </div>
                        </div>
                    ) : (
                        <div className="space-y-4">
                            {messages.map((msg) => (
                                <div
                                    key={msg.id}
                                    className={`flex ${msg.type === "user" ? "justify-end" : "justify-start"}`}
                                >
                                    <div
                                        className={`max-w-[85%] ${msg.type === "user"
                                            ? "bg-gradient-to-br from-violet-600 to-purple-600 rounded-2xl rounded-br-md"
                                            : "bg-[#151d2d] border border-white/5 rounded-2xl rounded-bl-md"
                                            } p-4`}
                                    >
                                        {/* Mode & Time Badge */}
                                        {msg.type === "assistant" && (
                                            <div className="flex items-center gap-2 mb-3">
                                                <div
                                                    className={`flex items-center gap-1.5 px-2 py-1 rounded-md text-xs font-medium ${msg.mode === "planning"
                                                        ? "bg-blue-500/20 text-blue-400"
                                                        : "bg-amber-500/20 text-amber-400"
                                                        }`}
                                                >
                                                    {msg.mode === "planning" ? (
                                                        <Brain className="w-3 h-3" />
                                                    ) : (
                                                        <Zap className="w-3 h-3" />
                                                    )}
                                                    {msg.mode === "planning" ? "Planning" : "Fast"}
                                                </div>
                                                <span className="text-xs text-gray-500">
                                                    {formatTime(msg.timestamp)}
                                                </span>
                                                {msg.metadata?.success !== undefined && (
                                                    <div
                                                        className={`flex items-center gap-1 text-xs ${msg.metadata.success ? "text-emerald-400" : "text-red-400"}`}
                                                    >
                                                        {msg.metadata.success ? (
                                                            <CheckCircle2 className="w-3 h-3" />
                                                        ) : (
                                                            <XCircle className="w-3 h-3" />
                                                        )}
                                                    </div>
                                                )}
                                            </div>
                                        )}

                                        {/* User timestamp */}
                                        {msg.type === "user" && (
                                            <div className="flex justify-end mb-2">
                                                <span className="text-xs text-white/60">
                                                    {formatTime(msg.timestamp)}
                                                </span>
                                            </div>
                                        )}

                                        {/* Content */}
                                        <div
                                            className={`prose prose-sm max-w-none ${msg.type === "user" ? "text-white" : "prose-invert"}`}
                                        >
                                            <ReactMarkdown
                                                components={{
                                                    strong: ({ children }) => (
                                                        <span className="font-semibold text-cyan-400">
                                                            {children}
                                                        </span>
                                                    ),
                                                    p: ({ children }) => (
                                                        <p className="mb-2 last:mb-0 text-gray-200 leading-relaxed">
                                                            {children}
                                                        </p>
                                                    ),
                                                    ul: ({ children }) => (
                                                        <ul className="list-disc pl-4 mb-2 text-gray-200">
                                                            {children}
                                                        </ul>
                                                    ),
                                                    ol: ({ children }) => (
                                                        <ol className="list-decimal pl-4 mb-2 text-gray-200">
                                                            {children}
                                                        </ol>
                                                    ),
                                                    li: ({ children }) => (
                                                        <li className="mb-1 text-gray-200">{children}</li>
                                                    ),
                                                    code: ({ children }) => (
                                                        <code className="bg-black/30 px-1.5 py-0.5 rounded text-sm text-emerald-400 font-mono">
                                                            {children}
                                                        </code>
                                                    ),
                                                    table: ({ children }) => (
                                                        <div className="overflow-x-auto my-3 rounded-lg border border-white/10">
                                                            <table className="w-full text-sm">
                                                                {children}
                                                            </table>
                                                        </div>
                                                    ),
                                                    thead: ({ children }) => (
                                                        <thead className="bg-white/5 text-gray-300">
                                                            {children}
                                                        </thead>
                                                    ),
                                                    th: ({ children }) => (
                                                        <th className="px-3 py-2 text-left font-medium border-b border-white/10">
                                                            {children}
                                                        </th>
                                                    ),
                                                    td: ({ children }) => (
                                                        <td className="px-3 py-2 text-gray-400 border-b border-white/5">
                                                            {children}
                                                        </td>
                                                    ),
                                                }}
                                            >
                                                {msg.content}
                                            </ReactMarkdown>
                                        </div>

                                        {/* Metadata */}
                                        {msg.type === "assistant" && msg.metadata?.sql && (
                                            <div className="mt-4 pt-3 border-t border-white/10">
                                                <button
                                                    type="button"
                                                    onClick={() => toggleSql(msg.id)}
                                                    className="flex items-center gap-2 text-xs text-gray-400 hover:text-white transition-colors"
                                                >
                                                    <Code className="w-3.5 h-3.5" />
                                                    <span>Generated SQL</span>
                                                    <ChevronDown
                                                        className={`w-3.5 h-3.5 transition-transform ${sqlExpanded[msg.id] ? "rotate-180" : ""}`}
                                                    />
                                                </button>
                                                {sqlExpanded[msg.id] && (
                                                    <pre className="mt-2 p-3 bg-black/40 rounded-lg text-xs text-emerald-400 font-mono overflow-x-auto">
                                                        {msg.metadata.sql}
                                                    </pre>
                                                )}
                                            </div>
                                        )}

                                        {/* Timing */}
                                        {msg.type === "assistant" && msg.metadata?.timing && (
                                            <div className="mt-3 flex items-center gap-2 text-xs text-gray-500">
                                                <Clock className="w-3.5 h-3.5" />
                                                <span>
                                                    {msg.metadata.timing.total_time
                                                        ? `${msg.metadata.timing.total_time}s`
                                                        : msg.metadata.timing.total
                                                            ? `${msg.metadata.timing.total}s`
                                                            : "N/A"}
                                                </span>
                                            </div>
                                        )}
                                    </div>
                                </div>
                            ))}

                            {/* Loading */}
                            {loading && (
                                <div className="flex justify-start">
                                    <div className="bg-[#151d2d] border border-white/5 rounded-2xl rounded-bl-md p-4">
                                        <div className="flex items-center gap-3">
                                            <div className="relative">
                                                <Loader2 className="w-5 h-5 animate-spin text-violet-400" />
                                            </div>
                                            <span className="text-gray-400 text-sm">
                                                {mode === "planning"
                                                    ? "Analyzing with SAGE-CODE..."
                                                    : "Generating SQL..."}
                                            </span>
                                        </div>
                                    </div>
                                </div>
                            )}

                            <div ref={messagesEndRef} />
                        </div>
                    )}
                </div>

                {/* Input Area */}
                <div className="mt-4 relative">
                    <div className="flex items-center gap-3 p-2 bg-[#0d1520] border border-white/10 rounded-2xl focus-within:border-violet-500/50 focus-within:ring-2 focus-within:ring-violet-500/20 transition-all">
                        <input
                            type="text"
                            value={input}
                            onChange={(e) => setInput(e.target.value)}
                            onKeyPress={handleKeyPress}
                            placeholder="Ask a question about your clinical trial data..."
                            className="flex-1 px-4 py-3 bg-transparent text-white placeholder-gray-500 focus:outline-none text-sm"
                            disabled={loading}
                        />
                        <button
                            type="button"
                            onClick={handleSend}
                            disabled={loading || !input.trim()}
                            className={`flex items-center gap-2 px-5 py-3 rounded-xl font-medium text-sm transition-all ${loading || !input.trim()
                                ? "bg-gray-800 text-gray-500 cursor-not-allowed"
                                : mode === "planning"
                                    ? "bg-gradient-to-r from-blue-600 to-blue-500 text-white hover:shadow-lg hover:shadow-blue-500/25"
                                    : "bg-gradient-to-r from-amber-500 to-orange-500 text-white hover:shadow-lg hover:shadow-orange-500/25"
                                }`}
                        >
                            {loading ? (
                                <Loader2 className="w-4 h-4 animate-spin" />
                            ) : (
                                <Send className="w-4 h-4" />
                            )}
                            <span>Send</span>
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
}
