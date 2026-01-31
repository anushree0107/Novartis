import { Button } from "../ui/badge";

// Simple cn utility inline
const cn = (...classes: (string | undefined | false)[]) => classes.filter(Boolean).join(' ');

// Icons
const CheckCircle = () => (
    <svg className="h-8 w-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
    </svg>
);

const Eye = () => (
    <svg className="h-8 w-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
    </svg>
);

const AlertTriangle = () => (
    <svg className="h-8 w-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
    </svg>
);

interface Verdict {
    decision: "CLEAR" | "WATCH" | "ALERT";
    confidence: number;
    reasoning: string;
    recommendation: string;
}

interface Agent {
    id: string;
    name: string;
    role: string;
    avatar: string;
}

interface VerdictCardProps {
    verdict: Verdict;
    judge: Agent;
}

const verdictStyles = {
    CLEAR: {
        bg: "bg-emerald-500/10",
        border: "border-emerald-500/30",
        text: "text-emerald-400",
        barBg: "bg-emerald-500",
        icon: CheckCircle,
        label: "Clear",
    },
    WATCH: {
        bg: "bg-amber-500/10",
        border: "border-amber-500/30",
        text: "text-amber-400",
        barBg: "bg-amber-500",
        icon: Eye,
        label: "Watch",
    },
    ALERT: {
        bg: "bg-red-500/10",
        border: "border-red-500/30",
        text: "text-red-400",
        barBg: "bg-red-500",
        icon: AlertTriangle,
        label: "Alert",
    },
};

export function VerdictCard({ verdict, judge }: VerdictCardProps) {
    const style = verdictStyles[verdict.decision];
    const Icon = style.icon;

    return (
        <div className="rounded-lg border border-gray-700 bg-gray-800/50">
            {/* Header */}
            <div className="flex items-center gap-3 border-b border-gray-700 px-4 py-3">
                <div className="flex h-8 w-8 items-center justify-center rounded-full bg-cyan-500 text-sm font-bold text-white">
                    {judge.avatar}
                </div>
                <div>
                    <h3 className="text-sm font-semibold uppercase tracking-wider text-gray-400">Final Verdict</h3>
                    <p className="text-xs text-gray-500">
                        Delivered by {judge.name}, {judge.role}
                    </p>
                </div>
            </div>

            {/* Content */}
            <div className="p-4">
                <div className="flex flex-col gap-6 lg:flex-row">
                    {/* Verdict Badge */}
                    <div className="flex flex-col items-center rounded-lg border border-gray-700 bg-gray-700/50 p-6">
                        <div
                            className={cn("flex h-16 w-16 items-center justify-center rounded-full border", style.bg, style.border, style.text)}
                        >
                            <Icon />
                        </div>
                        <span className={cn("mt-3 text-2xl font-bold", style.text)}>{verdict.decision}</span>
                        <span className="text-sm text-gray-400">{style.label}</span>

                        {/* Confidence Meter */}
                        <div className="mt-4 w-full">
                            <div className="mb-1 flex justify-between text-xs">
                                <span className="text-gray-400">Confidence</span>
                                <span className={style.text}>{verdict.confidence}%</span>
                            </div>
                            <div className="h-2 w-full overflow-hidden rounded-full bg-gray-700">
                                <div
                                    className={cn("h-full rounded-full", style.barBg)}
                                    style={{ width: `${verdict.confidence}%` }}
                                />
                            </div>
                        </div>
                    </div>

                    {/* Details */}
                    <div className="flex-1 space-y-4">
                        <div>
                            <h4 className="mb-2 text-sm font-semibold text-white">Reasoning</h4>
                            <p className="text-sm leading-relaxed text-gray-400">{verdict.reasoning}</p>
                        </div>

                        <div>
                            <h4 className="mb-2 text-sm font-semibold text-white">Recommendation</h4>
                            <p className="text-sm leading-relaxed text-gray-400">{verdict.recommendation}</p>
                        </div>

                        {/* Actions */}
                        <div className="flex flex-wrap gap-2 pt-2">
                            <Button variant="outline" size="sm" className="gap-2">
                                <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                                </svg>
                                View Details
                            </Button>
                            <Button size="sm" className="gap-2">
                                Take Action
                            </Button>
                            <Button variant="ghost" size="sm" className="gap-2">
                                <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                                </svg>
                                Dismiss
                            </Button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
