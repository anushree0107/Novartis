import { Badge } from "../ui/badge";

// Simple cn utility inline
const cn = (...classes: (string | undefined | false)[]) => classes.filter(Boolean).join(' ');

interface TranscriptEntry {
    id: string;
    agentId: string;
    round: number;
    content: string;
    keyPoints: string[];
    sentiment: "critical" | "optimistic" | "neutral";
}

interface Agent {
    id: string;
    name: string;
    role: string;
    avatar: string;
}

interface DebateTranscriptProps {
    transcript: TranscriptEntry[];
    agents: Agent[];
}

const agentStyles: Record<string, { bg: string; border: string; text: string; bubble: string; solidBg: string }> = {
    hawk: {
        bg: "bg-red-500/20",
        border: "border-red-500/30",
        text: "text-red-400",
        bubble: "bg-red-500/10 border-l-red-500",
        solidBg: "bg-red-500",
    },
    dove: {
        bg: "bg-emerald-500/20",
        border: "border-emerald-500/30",
        text: "text-emerald-400",
        bubble: "bg-emerald-500/10 border-l-emerald-500",
        solidBg: "bg-emerald-500",
    },
    owl: {
        bg: "bg-cyan-500/20",
        border: "border-cyan-500/30",
        text: "text-cyan-400",
        bubble: "bg-cyan-500/10 border-l-cyan-500",
        solidBg: "bg-cyan-500",
    },
};

const sentimentIcons: Record<string, { icon: string; color: string }> = {
    critical: { icon: "↓", color: "text-red-400" },
    optimistic: { icon: "+", color: "text-emerald-400" },
    neutral: { icon: "~", color: "text-cyan-400" },
};

export function DebateTranscript({ transcript, agents }: DebateTranscriptProps) {
    const getAgent = (agentId: string) => agents.find((a) => a.id === agentId);

    // Group by rounds
    const rounds = transcript.reduce(
        (acc, entry) => {
            if (!acc[entry.round]) {
                acc[entry.round] = [];
            }
            acc[entry.round].push(entry);
            return acc;
        },
        {} as Record<number, TranscriptEntry[]>
    );

    return (
        <div className="space-y-6">
            {Object.entries(rounds).map(([round, entries]) => (
                <div key={round}>
                    <div className="mb-3 flex items-center gap-2">
                        <div className="h-px flex-1 bg-gray-700" />
                        <Badge variant="outline" className="font-mono text-xs">
                            Round {round}
                        </Badge>
                        <div className="h-px flex-1 bg-gray-700" />
                    </div>

                    <div className="space-y-4">
                        {entries.map((entry) => {
                            const agent = getAgent(entry.agentId);
                            if (!agent) return null;

                            return (
                                <div key={entry.id} className="flex gap-3">
                                    {/* Avatar */}
                                    <div
                                        className={cn(
                                            "flex h-10 w-10 shrink-0 items-center justify-center rounded-full text-sm font-bold text-white",
                                            agentStyles[entry.agentId]?.solidBg
                                        )}
                                    >
                                        {agent.avatar}
                                    </div>

                                    {/* Content */}
                                    <div className="flex-1">
                                        <div className="mb-1 flex items-center gap-2">
                                            <span className={cn("font-semibold", agentStyles[entry.agentId]?.text)}>{agent.name}</span>
                                            <span className="text-xs text-gray-400">{agent.role}</span>
                                            <span className={cn("text-xs", sentimentIcons[entry.sentiment]?.color)}>
                                                {sentimentIcons[entry.sentiment]?.icon}
                                            </span>
                                        </div>

                                        <div
                                            className={cn(
                                                "rounded-lg border-l-4 p-3",
                                                agentStyles[entry.agentId]?.bubble
                                            )}
                                        >
                                            <p className="text-sm leading-relaxed text-gray-200">{entry.content}</p>

                                            {entry.keyPoints.length > 0 && (
                                                <div className="mt-2 flex flex-wrap gap-1">
                                                    {entry.keyPoints.map((point) => (
                                                        <Badge
                                                            key={point}
                                                            variant="outline"
                                                            className={cn(
                                                                "text-xs font-normal",
                                                                agentStyles[entry.agentId]?.border,
                                                                agentStyles[entry.agentId]?.text
                                                            )}
                                                        >
                                                            {point}
                                                        </Badge>
                                                    ))}
                                                </div>
                                            )}
                                        </div>
                                    </div>
                                </div>
                            );
                        })}
                    </div>
                </div>
            ))}
        </div>
    );
}
