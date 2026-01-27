import { useState, useRef, useEffect } from 'react';
import { Send, Loader2, Brain, Zap, Code, Clock } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import { executeQuery, executeNexusQuery, QueryResponse, NexusQueryResponse } from '../services/api';

type QueryMode = 'planning' | 'fast';

interface Message {
    id: string;
    type: 'user' | 'assistant';
    content: string;
    mode: QueryMode;
    timestamp: Date;
    metadata?: {
        sql?: string;
        timing?: Record<string, number>;
        success?: boolean;
        error?: string;
        executionResult?: any;
    };
}

export function Chat() {
    const [mode, setMode] = useState<QueryMode>('fast');
    const [input, setInput] = useState('');
    const [messages, setMessages] = useState<Message[]>([]);
    const [loading, setLoading] = useState(false);
    const messagesEndRef = useRef<HTMLDivElement>(null);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    const exampleQueries = [
        'How many studies are in the database?',
        'What is the average DQI score across all sites?',
        'Which sites have critical alerts?',
        'Show enrollment status by region',
    ];

    const handleSend = async () => {
        if (!input.trim() || loading) return;

        const userMessage: Message = {
            id: Date.now().toString(),
            type: 'user',
            content: input,
            mode,
            timestamp: new Date(),
        };

        setMessages(prev => [...prev, userMessage]);
        setInput('');
        setLoading(true);

        try {
            let response: Message;

            if (mode === 'fast') {
                // Fast Mode - Trials Text-to-SQL
                const result: NexusQueryResponse = await executeNexusQuery(input);

                // Format execution result as the main answer if available
                let mainContent = '';
                if (result.execution_result && result.execution_result.data && result.execution_result.data.length > 0) {
                    const data = result.execution_result.data;
                    const columns = result.execution_result.columns || Object.keys(data[0]);

                    // Create markdown table
                    let table = '| ' + columns.join(' | ') + ' |\n';
                    table += '| ' + columns.map(() => '---').join(' | ') + ' |\n';
                    data.slice(0, 20).forEach((row: any) => {
                        const values = columns.map((col: string) => String(row[col] ?? ''));
                        table += '| ' + values.join(' | ') + ' |\n';
                    });
                    if (data.length > 20) {
                        table += `\n*Showing 20 of ${data.length} rows*`;
                    }
                    mainContent = `**Query Results (${data.length} rows):**\n\n${table}`;
                } else if (result.explanation) {
                    mainContent = result.explanation;
                } else {
                    mainContent = 'Query executed successfully. No results returned.';
                }

                response = {
                    id: (Date.now() + 1).toString(),
                    type: 'assistant',
                    content: mainContent,
                    mode: 'fast',
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
                // Planning Mode - SAGE-CODE
                const result: QueryResponse = await executeQuery(input);
                response = {
                    id: (Date.now() + 1).toString(),
                    type: 'assistant',
                    content: result.answer,
                    mode: 'planning',
                    timestamp: new Date(),
                    metadata: {
                        timing: result.timing,
                        success: result.success,
                    },
                };
            }

            setMessages(prev => [...prev, response]);
        } catch (error: any) {
            const errorMessage: Message = {
                id: (Date.now() + 1).toString(),
                type: 'assistant',
                content: `Error: ${error.message || 'Failed to process query'}`,
                mode,
                timestamp: new Date(),
                metadata: { success: false, error: error.message },
            };
            setMessages(prev => [...prev, errorMessage]);
        } finally {
            setLoading(false);
        }
    };

    const handleKeyPress = (e: React.KeyboardEvent) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSend();
        }
    };

    return (
        <div className="flex flex-col h-[calc(100vh-180px)]">
            {/* Header with Mode Toggle */}
            <div className="flex items-center justify-between mb-4">
                <div>
                    <h2 className="text-xl font-semibold bg-gradient-to-r from-[#60a5fa] to-[#3b82f6] bg-clip-text text-transparent">
                        AI Query Assistant
                    </h2>
                    <p className="text-gray-300 text-sm">
                        Ask questions about your clinical trial data
                    </p>
                </div>

                {/* Mode Toggle */}
                <div className="flex bg-[#0f1419] rounded-lg p-1">
                    <button
                        onClick={() => setMode('planning')}
                        className={`flex items-center gap-2 px-4 py-2 rounded-md text-sm font-medium transition-all ${mode === 'planning'
                            ? 'bg-[#1a2332] text-blue-400 shadow-sm'
                            : 'text-gray-300 hover:text-white'
                            }`}
                    >
                        <Brain className="w-4 h-4" />
                        Planning
                    </button>
                    <button
                        onClick={() => setMode('fast')}
                        className={`flex items-center gap-2 px-4 py-2 rounded-md text-sm font-medium transition-all ${mode === 'fast'
                            ? 'bg-[#1a2332] text-orange-400 shadow-sm'
                            : 'text-gray-300 hover:text-white'
                            }`}
                    >
                        <Zap className="w-4 h-4" />
                        Fast
                    </button>
                </div>
            </div>

            {/* Mode Description */}
            <div className={`mb-4 p-3 rounded-lg text-sm ${mode === 'planning'
                ? 'bg-blue-900/30 text-blue-300 border border-blue-500/30'
                : 'bg-orange-900/30 text-orange-300 border border-orange-500/30'
                }`}>
                {mode === 'planning' ? (
                    <div className="flex items-center gap-2">
                        <Brain className="w-4 h-4" />
                        <span><strong>Planning Mode:</strong> Uses SAGE-CODE with graph reasoning for detailed analysis</span>
                    </div>
                ) : (
                    <div className="flex items-center gap-2">
                        <Zap className="w-4 h-4" />
                        <span><strong>Fast Mode:</strong> Trials Text-to-SQL pipeline for quick SQL generation</span>
                    </div>
                )}
            </div>

            {/* Chat Messages */}
            <div className="flex-1 overflow-y-auto bg-[#0f1419] rounded-lg p-4 space-y-4">
                {messages.length === 0 ? (
                    <div className="text-center text-gray-400 py-8">
                        <p className="mb-4">Start a conversation by asking a question</p>
                        <div className="flex flex-wrap justify-center gap-2">
                            {exampleQueries.map((query, idx) => (
                                <button
                                    key={idx}
                                    onClick={() => setInput(query)}
                                    className="px-3 py-1.5 bg-[#1a2332] text-gray-200 text-sm rounded-full border border-white/10 hover:border-blue-400 hover:text-blue-400 transition-colors"
                                >
                                    {query}
                                </button>
                            ))}
                        </div>
                    </div>
                ) : (
                    messages.map((msg) => (
                        <div
                            key={msg.id}
                            className={`flex ${msg.type === 'user' ? 'justify-end' : 'justify-start'}`}
                        >
                            <div
                                className={`max-w-[80%] rounded-lg p-4 ${msg.type === 'user'
                                    ? 'bg-blue-600 text-white'
                                    : 'bg-[#1a2332] border border-white/10 shadow-sm'
                                    }`}
                            >
                                {/* Mode Badge for Assistant */}
                                {msg.type === 'assistant' && (
                                    <div className={`flex items-center gap-1 text-xs mb-2 ${msg.mode === 'planning' ? 'text-blue-400' : 'text-orange-400'
                                        }`}>
                                        {msg.mode === 'planning' ? <Brain className="w-3 h-3" /> : <Zap className="w-3 h-3" />}
                                        {msg.mode === 'planning' ? 'Planning Mode' : 'Fast Mode'}
                                    </div>
                                )}

                                {/* Message Content */}
                                <div className={`prose prose-sm max-w-none ${msg.type === 'user' ? 'prose-invert' : 'prose-invert'}`}>
                                    <ReactMarkdown
                                        components={{
                                            strong: ({ children }) => <span className="font-semibold text-blue-400">{children}</span>,
                                            p: ({ children }) => <p className="mb-2 last:mb-0 text-gray-100">{children}</p>,
                                            ul: ({ children }) => <ul className="list-disc pl-4 mb-2 text-gray-100">{children}</ul>,
                                            ol: ({ children }) => <ol className="list-decimal pl-4 mb-2 text-gray-100">{children}</ol>,
                                            li: ({ children }) => <li className="mb-1 text-gray-100">{children}</li>,
                                            code: ({ children }) => <code className="bg-[#0f1419] px-1 rounded text-sm text-green-400">{children}</code>,
                                        }}
                                    >
                                        {msg.content}
                                    </ReactMarkdown>
                                </div>

                                {/* Metadata (SQL, Timing) */}
                                {msg.type === 'assistant' && msg.metadata && (
                                    <div className="mt-3 pt-3 border-t border-white/10 space-y-2">
                                        {/* SQL */}
                                        {msg.metadata.sql && (
                                            <div className="bg-gray-900 text-green-400 p-2 rounded text-xs font-mono overflow-x-auto">
                                                <div className="flex items-center gap-1 text-gray-400 mb-1">
                                                    <Code className="w-3 h-3" />
                                                    SQL
                                                </div>
                                                {msg.metadata.sql}
                                            </div>
                                        )}

                                        {/* Timing */}
                                        {msg.metadata.timing && (
                                            <div className="flex items-center gap-2 text-xs text-gray-500">
                                                <Clock className="w-3 h-3" />
                                                <span>
                                                    {msg.metadata.timing.total_time
                                                        ? `${msg.metadata.timing.total_time}s`
                                                        : msg.metadata.timing.total
                                                            ? `${msg.metadata.timing.total}s`
                                                            : 'N/A'
                                                    }
                                                </span>
                                                {msg.metadata.success !== undefined && (
                                                    <span className={msg.metadata.success ? 'text-green-600' : 'text-red-600'}>
                                                        {msg.metadata.success ? '✓ Success' : '✗ Failed'}
                                                    </span>
                                                )}
                                            </div>
                                        )}

                                        {/* Execution Result Preview */}
                                        {msg.metadata.executionResult && (
                                            <details className="text-xs">
                                                <summary className="cursor-pointer text-blue-400 hover:underline">
                                                    View Execution Result
                                                </summary>
                                                <pre className="bg-[#0f1419] p-2 rounded mt-1 overflow-x-auto text-gray-200">
                                                    {JSON.stringify(msg.metadata.executionResult, null, 2)}
                                                </pre>
                                            </details>
                                        )}
                                    </div>
                                )}
                            </div>
                        </div>
                    ))
                )}

                {/* Loading Indicator */}
                {loading && (
                    <div className="flex justify-start">
                        <div className="bg-[#1a2332] border border-white/10 shadow-sm rounded-lg p-4 flex items-center gap-2">
                            <Loader2 className="w-4 h-4 animate-spin text-blue-400" />
                            <span className="text-gray-300">
                                {mode === 'planning' ? 'Analyzing with SAGE-CODE...' : 'Generating SQL...'}
                            </span>
                        </div>
                    </div>
                )}

                <div ref={messagesEndRef} />
            </div>

            {/* Input Area */}
            <div className="mt-4 flex gap-2">
                <input
                    type="text"
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyPress={handleKeyPress}
                    placeholder="Ask a question about your clinical trial data..."
                    className="flex-1 px-4 py-3 bg-[#0f1419] border border-white/10 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    disabled={loading}
                />
                <button
                    onClick={handleSend}
                    disabled={loading || !input.trim()}
                    className={`px-6 py-3 rounded-lg font-medium flex items-center gap-2 transition-colors ${loading || !input.trim()
                        ? 'bg-gray-700 text-gray-400 cursor-not-allowed'
                        : mode === 'planning'
                            ? 'bg-blue-600 text-white hover:bg-blue-700'
                            : 'bg-orange-500 text-white hover:bg-orange-600'
                        }`}
                >
                    {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
                    Send
                </button>
            </div>
        </div>
    );
}
