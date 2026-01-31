import { useState, useRef, useEffect } from 'react';
import { AgentPanel } from './debate/agent-panel';
import { DebateTranscript } from './debate/debate-transcript';
import { VerdictCard } from './debate/verdict-card';
import { Badge, Button } from './ui/badge';
import { Play, RotateCcw, Download, ChevronDown, ChevronUp } from 'lucide-react';

interface DebateMessage {
    type: 'message' | 'verdict' | 'status' | 'trace' | 'error';
    speaker: string;
    content: string;
}

// Utility to strip markdown
const stripMarkdown = (text: string): string => {
    if (!text) return '';
    return text
        .replace(/\*\*(.+?)\*\*/g, '$1')
        .replace(/__(.+?)__/g, '$1')
        .replace(/^#{1,6}\s+/gm, '')
        .replace(/\*\*/g, '')
        .trim();
};

// Default agents configuration
const defaultAgents = [
    { id: 'hawk', name: 'Hawk', role: 'Risk Analyzer', avatar: 'H' },
    { id: 'dove', name: 'Dove', role: 'Advocate', avatar: 'D' },
    { id: 'owl', name: 'Owl', role: 'Chief Judge', avatar: 'O' },
];

// Extract key points from message
const extractKeyPoints = (content: string): string[] => {
    const points: string[] = [];
    const patterns = [
        /zero records/gi,
        /missing pages/gi,
        /no.*connections/gi,
        /data absence/gi,
        /new.*entity/gi,
        /integration/gi,
        /potential/gi,
        /opportunity/gi,
        /risk/gi,
        /concern/gi,
        /scrutiny/gi,
    ];

    patterns.forEach(pattern => {
        const match = content.match(pattern);
        if (match) {
            points.push(match[0].charAt(0).toUpperCase() + match[0].slice(1).toLowerCase());
        }
    });

    return [...new Set(points)].slice(0, 3);
};

// Parse verdict from content
const parseVerdict = (content: string) => {
    const verdictMatch = content.match(/Verdict:\s*(\w+)/i);
    const decision = verdictMatch ? verdictMatch[1].toUpperCase() as 'CLEAR' | 'WATCH' | 'ALERT' : 'WATCH';

    const reasoningMatch = content.match(/Reasoning:?\s*([^]*?)(?=Recommendation:|$)/i);
    const reasoning = reasoningMatch ? stripMarkdown(reasoningMatch[1].trim()) : stripMarkdown(content);

    const recommendationMatch = content.match(/Recommendation:?\s*([^]*?)$/i);
    const recommendation = recommendationMatch ? stripMarkdown(recommendationMatch[1].trim()) : '';

    return {
        decision,
        confidence: 78,
        reasoning,
        recommendation,
    };
};

export function DebateCouncil() {
    const [nodeId, setNodeId] = useState('');
    const [messages, setMessages] = useState<DebateMessage[]>([]);
    const [isDebating, setIsDebating] = useState(false);
    const [status, setStatus] = useState<'idle' | 'in-progress' | 'concluded'>('idle');
    const [isTranscriptExpanded, setIsTranscriptExpanded] = useState(true);
    const wsRef = useRef<WebSocket | null>(null);
    const messagesEndRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages]);

    const startDebate = () => {
        if (!nodeId.trim()) return;

        setMessages([]);
        setIsDebating(true);
        setStatus('in-progress');

        const wsUrl = `ws://localhost:8000/api/debate/ws/debate/${encodeURIComponent(nodeId.trim())}`;
        const ws = new WebSocket(wsUrl);
        wsRef.current = ws;

        ws.onopen = () => setIsDebating(true);

        ws.onmessage = (event) => {
            try {
                const data: DebateMessage = JSON.parse(event.data);
                if (data.type !== 'status') {
                    setMessages(prev => [...prev, data]);
                }
            } catch (e) {
                console.error('Failed to parse message:', e);
            }
        };

        ws.onclose = () => {
            setIsDebating(false);
            setStatus('concluded');
            wsRef.current = null;
        };

        ws.onerror = () => {
            setIsDebating(false);
            setStatus('idle');
        };
    };

    const restartDebate = () => {
        wsRef.current?.close();
        setMessages([]);
        setStatus('idle');
        setNodeId('');
    };

    const exportDebate = () => {
        const content = messages.map(m => `[${m.speaker}]: ${m.content}`).join('\n\n');
        const blob = new Blob([content], { type: 'text/plain' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `debate-${nodeId}-${Date.now()}.txt`;
        a.click();
    };

    // Transform messages into transcript format
    const transcript = messages
        .filter(m => m.type === 'message' && ['Hawk', 'Dove', 'Owl'].includes(m.speaker))
        .map((m, index, arr) => {
            const hawkDoveMessages = arr.filter((msg, i) =>
                i <= index && ['Hawk', 'Dove'].includes(msg.speaker)
            );
            const round = Math.ceil(hawkDoveMessages.length / 2) || 1;

            return {
                id: String(index),
                agentId: m.speaker.toLowerCase(),
                round,
                content: stripMarkdown(m.content),
                keyPoints: extractKeyPoints(m.content),
                sentiment: m.speaker === 'Hawk' ? 'critical' as const :
                    m.speaker === 'Dove' ? 'optimistic' as const : 'neutral' as const,
            };
        });

    const verdictMessage = messages.find(m => m.type === 'verdict');
    const verdict = verdictMessage ? parseVerdict(verdictMessage.content) : null;

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div className="flex items-center gap-4">
                    <h1 className="text-2xl font-bold text-white">Debate Council</h1>
                    {nodeId && (
                        <Badge variant="outline" className="font-mono">
                            Node: {nodeId}
                        </Badge>
                    )}
                    {status !== 'idle' && (
                        <Badge
                            variant="outline"
                            className={
                                status === 'concluded'
                                    ? 'border-emerald-500/30 bg-emerald-500/10 text-emerald-400'
                                    : 'border-cyan-500/30 bg-cyan-500/10 text-cyan-400'
                            }
                        >
                            {status === 'concluded' ? 'Concluded' : 'In Progress'}
                        </Badge>
                    )}
                </div>

                <div className="flex items-center gap-2">
                    {status === 'concluded' && (
                        <>
                            <Button variant="outline" size="sm" className="gap-2" onClick={exportDebate}>
                                <Download className="h-4 w-4" />
                                Export
                            </Button>
                            <Button variant="outline" size="sm" className="gap-2" onClick={restartDebate}>
                                <RotateCcw className="h-4 w-4" />
                                Restart
                            </Button>
                        </>
                    )}
                    {status === 'idle' && (
                        <>
                            <input
                                type="text"
                                value={nodeId}
                                onChange={(e) => setNodeId(e.target.value)}
                                placeholder="Enter Node ID..."
                                className="px-4 py-2 w-40 bg-gray-800 border border-gray-600 rounded-lg text-white text-sm placeholder-gray-500 focus:outline-none focus:border-cyan-500"
                                onKeyDown={(e) => e.key === 'Enter' && startDebate()}
                            />
                            <Button size="sm" className="gap-2 bg-cyan-500 hover:bg-cyan-400" onClick={startDebate} disabled={!nodeId.trim()}>
                                <Play className="h-4 w-4" />
                                Start Debate
                            </Button>
                        </>
                    )}
                    {isDebating && (
                        <Button variant="outline" size="sm" className="gap-2" onClick={() => wsRef.current?.close()}>
                            Stop
                        </Button>
                    )}
                </div>
            </div>

            {/* Agent Panel */}
            <AgentPanel agents={defaultAgents} status={status === 'concluded' ? 'concluded' : 'in-progress'} />

            {/* Transcript Section */}
            {transcript.length > 0 && (
                <div className="rounded-lg border border-gray-700 overflow-hidden">
                    <button
                        onClick={() => setIsTranscriptExpanded(!isTranscriptExpanded)}
                        className="flex w-full items-center justify-between bg-gray-800/50 px-4 py-3 hover:bg-gray-800 transition-colors"
                    >
                        <h2 className="text-sm font-semibold uppercase tracking-wider text-gray-400">
                            Debate Transcript
                        </h2>
                        {isTranscriptExpanded ? (
                            <ChevronUp className="h-4 w-4 text-gray-400" />
                        ) : (
                            <ChevronDown className="h-4 w-4 text-gray-400" />
                        )}
                    </button>

                    {isTranscriptExpanded && (
                        <div className="p-4 max-h-[400px] overflow-y-auto bg-gray-800/30">
                            <DebateTranscript transcript={transcript} agents={defaultAgents} />
                            <div ref={messagesEndRef} />
                        </div>
                    )}
                </div>
            )}

            {/* Verdict Section */}
            {status === 'concluded' && verdict && (
                <VerdictCard verdict={verdict} judge={defaultAgents.find(a => a.id === 'owl')!} />
            )}

            {/* Empty State */}
            {messages.length === 0 && status === 'idle' && (
                <div className="rounded-lg border border-gray-700 bg-gray-800/30 p-16 text-center">
                    <div className="flex justify-center gap-8 mb-6">
                        <div className="w-16 h-16 rounded-full bg-red-500/20 border-2 border-red-500/30 flex items-center justify-center text-2xl font-bold text-red-400/50">H</div>
                        <div className="w-16 h-16 rounded-full bg-emerald-500/20 border-2 border-emerald-500/30 flex items-center justify-center text-2xl font-bold text-emerald-400/50">D</div>
                        <div className="w-16 h-16 rounded-full bg-cyan-500/20 border-2 border-cyan-500/30 flex items-center justify-center text-2xl font-bold text-cyan-400/50">O</div>
                    </div>
                    <h3 className="text-xl font-medium text-gray-400 mb-2">Ready to Debate</h3>
                    <p className="text-sm text-gray-500">Enter a Node ID and click Start Debate to begin AI analysis</p>
                </div>
            )}
        </div>
    );
}
