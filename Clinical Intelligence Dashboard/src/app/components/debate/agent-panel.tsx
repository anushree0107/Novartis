// Simple cn utility inline
const cn = (...classes: (string | undefined | false)[]) => classes.filter(Boolean).join(' ');

interface Agent {
    id: string;
    name: string;
    role: string;
    avatar: string;
}

interface AgentPanelProps {
    agents: Agent[];
    status: "concluded" | "in-progress";
}

const agentStyles: Record<string, { bg: string; border: string; text: string; solid: string }> = {
    hawk: {
        bg: "bg-red-500/20",
        border: "border-red-500/50",
        text: "text-red-400",
        solid: "bg-red-500",
    },
    dove: {
        bg: "bg-emerald-500/20",
        border: "border-emerald-500/50",
        text: "text-emerald-400",
        solid: "bg-emerald-500",
    },
    owl: {
        bg: "bg-cyan-500/20",
        border: "border-cyan-500/50",
        text: "text-cyan-400",
        solid: "bg-cyan-500",
    },
};

export function AgentPanel({ agents, status }: AgentPanelProps) {
    return (
        <div className="rounded-lg border border-gray-700 bg-gray-800/30 p-8">
            <div className="flex items-center justify-center gap-6">
                {agents.map((agent, index) => (
                    <div key={agent.id} className="flex items-center gap-6">
                        {/* Agent Card */}
                        <div className="flex flex-col items-center">
                            <div
                                className={cn(
                                    "flex h-14 w-14 items-center justify-center rounded-full border-2 text-xl font-bold",
                                    agentStyles[agent.id]?.bg,
                                    agentStyles[agent.id]?.border,
                                    agentStyles[agent.id]?.text
                                )}
                            >
                                {agent.avatar}
                            </div>
                            <h3 className="mt-3 font-semibold text-white">{agent.name}</h3>
                            <p className="text-xs text-gray-400">{agent.role}</p>
                        </div>

                        {/* Connector Line */}
                        {index < agents.length - 1 && (
                            <div className="flex items-center gap-2">
                                <div className="h-px w-10 bg-gray-600" />
                                <svg className="h-3 w-3 text-gray-500" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                                </svg>
                                <div className="h-px w-10 bg-gray-600" />
                            </div>
                        )}
                    </div>
                ))}

                {/* Status Indicator */}
                <div className="ml-6 flex items-center gap-2 rounded-full border border-gray-600 bg-gray-700/50 px-4 py-2">
                    <span
                        className={cn(
                            "h-2 w-2 rounded-full",
                            status === "concluded" ? "bg-emerald-500" : "bg-cyan-500 animate-pulse"
                        )}
                    />
                    <span className="text-sm text-gray-300">
                        {status === "concluded" ? "Debate concluded" : "Debate in progress"}
                    </span>
                </div>
            </div>
        </div>
    );
}
