"use client";

import { useState, useEffect } from "react";
// @ts-expect-error - react-plotly.js lacks type declarations
import Plot from "react-plotly.js";
import {
    Box,
    Layers,
    Target,
    X,
    AlertTriangle,
    RefreshCw,
    Brain,
    TrendingUp,
    AlertCircle,
    Lightbulb,
    Info,
    ChevronRight,
} from "lucide-react";

interface Point3D {
    site_id: string;
    x: number;
    y: number;
    z: number;
    cluster_id: number;
    cluster_name: string;
    color: string;
    risk_level: string;
    tooltip: Record<string, number>;
}

interface ClusterInfo {
    cluster_id: number;
    name: string;
    size: number;
    risk_level: string;
    color: string;
    description: string;
}

interface Visualization3D {
    points: Point3D[];
    clusters: ClusterInfo[];
    method: string;
    total_sites: number;
    n_clusters: number;
}

interface SiteAnalysis {
    site_id: string;
    summary: string;
    risk_level: string;
    strengths: string[];
    concerns: string[];
    recommendations:
    | Array<{ priority: string; action: string; rationale: string }>
    | string[];
    cluster_context: string;
    cluster_color: { primary: string; secondary: string };
    risk_color: { bg: string; text: string };
}

const API_BASE_URL = "http://localhost:8000";

// Mock data for preview
const mockData: Visualization3D = {
    total_sites: 1605,
    n_clusters: 9,
    method: "ensemble",
    clusters: [
        { cluster_id: 0, name: "Cluster 0", size: 180, risk_level: "Low", color: "#06b6d4", description: "High performers" },
        { cluster_id: 1, name: "Cluster 1", size: 195, risk_level: "Low", color: "#8b5cf6", description: "Consistent" },
        { cluster_id: 2, name: "Cluster 2", size: 165, risk_level: "Medium", color: "#ec4899", description: "Moderate risk" },
        { cluster_id: 3, name: "Cluster 3", size: 210, risk_level: "Low", color: "#10b981", description: "Stable" },
        { cluster_id: 4, name: "Cluster 4", size: 175, risk_level: "Medium", color: "#f59e0b", description: "Variable" },
        { cluster_id: 5, name: "Cluster 5", size: 190, risk_level: "Low", color: "#3b82f6", description: "Strong" },
        { cluster_id: 6, name: "Cluster 6", size: 155, risk_level: "High", color: "#ef4444", description: "Needs attention" },
        { cluster_id: 7, name: "Cluster 7", size: 185, risk_level: "Low", color: "#14b8a6", description: "Excellent" },
        { cluster_id: 8, name: "Cluster 8", size: 150, risk_level: "Medium", color: "#f97316", description: "Improving" },
    ],
    points: Array.from({ length: 200 }, (_, i) => {
        const clusterId = i % 9;
        const colors = ["#06b6d4", "#8b5cf6", "#ec4899", "#10b981", "#f59e0b", "#3b82f6", "#ef4444", "#14b8a6", "#f97316"];
        const baseX = (clusterId % 3) * 4 - 4;
        const baseY = Math.floor(clusterId / 3) * 4 - 4;
        const baseZ = (clusterId % 2) * 6;
        return {
            site_id: `Site ${String(i + 1).padStart(4, "0")}`,
            x: baseX + (Math.random() - 0.5) * 3,
            y: baseY + (Math.random() - 0.5) * 3,
            z: baseZ + Math.random() * 8,
            cluster_id: clusterId,
            cluster_name: `Cluster ${clusterId}`,
            color: colors[clusterId],
            risk_level: ["Low", "Medium", "High"][Math.floor(Math.random() * 3)],
            tooltip: { dqi: Math.random() * 100, enrollment: Math.random() * 50 },
        };
    }),
};

export function Clustering3D() {
    const [data, setData] = useState<Visualization3D | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [selectedSite, setSelectedSite] = useState<string | null>(null);
    const [analysis, setAnalysis] = useState<SiteAnalysis | null>(null);
    const [analyzingLoading, setAnalyzingLoading] = useState(false);
    const [method, setMethod] = useState("ensemble");
    const [showModal, setShowModal] = useState(false);
    const [hoveredCluster, setHoveredCluster] = useState<number | null>(null);

    useEffect(() => {
        fetchData();
    }, [method]);

    const fetchData = async () => {
        setLoading(true);
        setError(null);
        try {
            const response = await fetch(
                `${API_BASE_URL}/api/analytics/clustering/advanced/3d?method=${method}`
            );
            if (!response.ok) throw new Error("Failed to fetch clustering data");
            const result = await response.json();
            setData(result);
        } catch {
            // Use mock data for preview
            setData(mockData);
        } finally {
            setLoading(false);
        }
    };

    const handlePointClick = async (siteId: string) => {
        setSelectedSite(siteId);
        setShowModal(true);
        setAnalyzingLoading(true);
        setAnalysis(null);

        try {
            const response = await fetch(
                `${API_BASE_URL}/api/analytics/clustering/advanced/analyze/site/${encodeURIComponent(siteId)}?method=${method}`
            );
            if (!response.ok) throw new Error("Failed to fetch analysis");
            const result = await response.json();
            setAnalysis(result);
        } catch {
            // Mock analysis for preview
            setAnalysis({
                site_id: siteId,
                summary: "This site demonstrates strong overall performance with consistent data quality metrics and enrollment rates above the study average.",
                risk_level: "Low",
                strengths: [
                    "Excellent data completeness rate (98.5%)",
                    "Strong enrollment velocity",
                    "Minimal protocol deviations",
                ],
                concerns: ["Minor delays in query resolution", "Some variability in visit scheduling"],
                recommendations: [
                    { priority: "Medium", action: "Implement automated query reminders", rationale: "Reduce resolution time" },
                    { priority: "Low", action: "Review visit scheduling process", rationale: "Improve consistency" },
                ],
                cluster_context: "This site belongs to a high-performing cluster with similar characteristics to 180 other sites.",
                cluster_color: { primary: "#06b6d4", secondary: "#0891b2" },
                risk_color: { bg: "#10b98120", text: "#10b981" },
            });
        } finally {
            setAnalyzingLoading(false);
        }
    };

    const closeModal = () => {
        setShowModal(false);
        setAnalysis(null);
        setSelectedSite(null);
    };

    const buildPlotData = () => {
        if (!data) return [];

        const clusterGroups: Record<number, Point3D[]> = {};
        data.points.forEach((point) => {
            if (!clusterGroups[point.cluster_id]) {
                clusterGroups[point.cluster_id] = [];
            }
            clusterGroups[point.cluster_id].push(point);
        });

        return Object.entries(clusterGroups).map(([clusterId, points]) => {
            const clusterInfo = data.clusters.find(
                (c) => c.cluster_id === parseInt(clusterId)
            );
            const isHovered = hoveredCluster === parseInt(clusterId);

            return {
                type: "scatter3d" as const,
                mode: "markers" as const,
                name: clusterInfo?.name || `Cluster ${clusterId}`,
                x: points.map((p) => p.x),
                y: points.map((p) => p.y),
                z: points.map((p) => p.z),
                text: points.map((p) => p.site_id),
                customdata: points.map((p) => ({
                    site_id: p.site_id,
                    risk_level: p.risk_level,
                    tooltip: p.tooltip,
                })),
                hovertemplate:
                    "<b>%{text}</b><br>" +
                    "Cluster: " +
                    (clusterInfo?.name || `Cluster ${clusterId}`) +
                    "<br>" +
                    "Risk: %{customdata.risk_level}<br>" +
                    "<extra></extra>",
                marker: {
                    size: isHovered ? 12 : 7,
                    color: points[0]?.color || "#6366F1",
                    opacity: isHovered ? 1 : 0.75,
                    line: {
                        color: "rgba(255,255,255,0.4)",
                        width: isHovered ? 2 : 1,
                    },
                },
            };
        });
    };

    const plotLayout = {
        autosize: true,
        height: 580,
        paper_bgcolor: "rgba(0,0,0,0)",
        plot_bgcolor: "rgba(0,0,0,0)",
        font: { color: "#94a3b8", family: "Inter, system-ui, sans-serif" },
        margin: { l: 0, r: 0, t: 0, b: 0 },
        showlegend: false,
        scene: {
            xaxis: {
                title: { text: "PC1", font: { size: 11 } },
                gridcolor: "rgba(148,163,184,0.1)",
                zerolinecolor: "rgba(148,163,184,0.2)",
                color: "#64748b",
                showbackground: true,
                backgroundcolor: "rgba(15,23,42,0.3)",
            },
            yaxis: {
                title: { text: "PC2", font: { size: 11 } },
                gridcolor: "rgba(148,163,184,0.1)",
                zerolinecolor: "rgba(148,163,184,0.2)",
                color: "#64748b",
                showbackground: true,
                backgroundcolor: "rgba(15,23,42,0.3)",
            },
            zaxis: {
                title: { text: "PC3", font: { size: 11 } },
                gridcolor: "rgba(148,163,184,0.1)",
                zerolinecolor: "rgba(148,163,184,0.2)",
                color: "#64748b",
                showbackground: true,
                backgroundcolor: "rgba(15,23,42,0.3)",
            },
            bgcolor: "rgba(0,0,0,0)",
            camera: {
                eye: { x: 1.5, y: 1.5, z: 1.2 },
            },
        },
    };

    const plotConfig = {
        displayModeBar: true,
        modeBarButtonsToRemove: [
            "toImage",
            "sendDataToCloud",
            "select2d",
            "lasso2d",
        ] as any[],
        displaylogo: false,
        modeBarStyle: { backgroundColor: "transparent" },
    };

    if (loading) {
        return (
            <div className="min-h-screen bg-[#0a0f18] p-8">
                <div className="flex items-center justify-center h-[600px]">
                    <div className="text-center">
                        <div className="relative w-16 h-16 mx-auto mb-6">
                            <div className="absolute inset-0 rounded-full border-4 border-cyan-500/20" />
                            <div className="absolute inset-0 rounded-full border-4 border-transparent border-t-cyan-500 animate-spin" />
                            <Box className="absolute inset-0 m-auto w-6 h-6 text-cyan-400" />
                        </div>
                        <p className="text-gray-400 font-medium">Loading 3D Clusters</p>
                        <p className="text-gray-500 text-sm mt-1">Preparing visualization...</p>
                    </div>
                </div>
            </div>
        );
    }

    if (error && !data) {
        return (
            <div className="min-h-screen bg-[#0a0f18] p-8">
                <div className="flex items-center justify-center h-[600px]">
                    <div className="text-center">
                        <div className="w-16 h-16 mx-auto mb-6 rounded-full bg-red-500/10 flex items-center justify-center">
                            <AlertTriangle className="w-8 h-8 text-red-400" />
                        </div>
                        <p className="text-red-400 font-medium mb-2">Failed to Load Data</p>
                        <p className="text-gray-500 text-sm mb-6">{error}</p>
                        <button
                            onClick={fetchData}
                            className="inline-flex items-center gap-2 px-5 py-2.5 bg-cyan-500/10 hover:bg-cyan-500/20 text-cyan-400 rounded-lg transition-colors"
                        >
                            <RefreshCw className="w-4 h-4" />
                            Try Again
                        </button>
                    </div>
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-[#0a0f18] text-white p-8">
            <div className="max-w-[1600px] mx-auto space-y-6">
                {/* Header */}
                <div className="flex items-start justify-between">
                    <div className="flex items-start gap-4">
                        <div className="relative">
                            <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-cyan-500 to-blue-600 flex items-center justify-center shadow-lg shadow-cyan-500/20">
                                <Layers className="w-6 h-6 text-white" />
                            </div>
                            <div className="absolute -bottom-1 -right-1 w-4 h-4 rounded-full bg-emerald-500 border-2 border-[#0a0f18]" />
                        </div>
                        <div>
                            <h1 className="text-2xl font-bold text-white">3D Site Clustering</h1>
                            <p className="text-gray-400 mt-0.5">
                                Click on any point to get AI-powered analysis
                            </p>
                        </div>
                    </div>

                    {/* Method Selector */}
                    <div className="flex items-center gap-3">
                        <span className="text-sm text-gray-400">Method</span>
                        <select
                            value={method}
                            onChange={(e) => setMethod(e.target.value)}
                            className="px-4 py-2 rounded-lg bg-[#0d1520] border border-white/10 text-white text-sm focus:outline-none focus:border-cyan-500/50 hover:border-white/20 transition-colors cursor-pointer"
                        >
                            <option value="ensemble">Ensemble</option>
                            <option value="hierarchical">Hierarchical</option>
                            <option value="gmm">GMM</option>
                        </select>
                    </div>
                </div>

                {/* Stats Cards */}
                {data && (
                    <div className="grid grid-cols-3 gap-4">
                        <div className="p-5 rounded-xl bg-[#0d1520]/80 border border-white/5 hover:border-cyan-500/30 transition-colors group">
                            <div className="flex items-center gap-3">
                                <div className="w-10 h-10 rounded-lg bg-cyan-500/10 flex items-center justify-center group-hover:bg-cyan-500/20 transition-colors">
                                    <Target className="w-5 h-5 text-cyan-400" />
                                </div>
                                <div>
                                    <div className="text-2xl font-bold text-white">
                                        {data.total_sites.toLocaleString()}
                                    </div>
                                    <div className="text-sm text-gray-500">Total Sites</div>
                                </div>
                            </div>
                        </div>

                        <div className="p-5 rounded-xl bg-[#0d1520]/80 border border-white/5 hover:border-violet-500/30 transition-colors group">
                            <div className="flex items-center gap-3">
                                <div className="w-10 h-10 rounded-lg bg-violet-500/10 flex items-center justify-center group-hover:bg-violet-500/20 transition-colors">
                                    <Box className="w-5 h-5 text-violet-400" />
                                </div>
                                <div>
                                    <div className="text-2xl font-bold text-white">{data.n_clusters}</div>
                                    <div className="text-sm text-gray-500">Clusters</div>
                                </div>
                            </div>
                        </div>

                        <div className="p-5 rounded-xl bg-[#0d1520]/80 border border-white/5 hover:border-emerald-500/30 transition-colors group">
                            <div className="flex items-center gap-3">
                                <div className="w-10 h-10 rounded-lg bg-emerald-500/10 flex items-center justify-center group-hover:bg-emerald-500/20 transition-colors">
                                    <Layers className="w-5 h-5 text-emerald-400" />
                                </div>
                                <div>
                                    <div className="text-2xl font-bold text-white capitalize">
                                        {data.method}
                                    </div>
                                    <div className="text-sm text-gray-500">Clustering Method</div>
                                </div>
                            </div>
                        </div>
                    </div>
                )}

                {/* Main Visualization */}
                <div className="grid grid-cols-[1fr_280px] gap-4">
                    {/* 3D Plot */}
                    <div className="rounded-2xl bg-[#0d1520]/60 border border-white/5 overflow-hidden">
                        <Plot
                            data={buildPlotData()}
                            layout={plotLayout as any}
                            config={plotConfig}
                            style={{ width: "100%", height: "580px" }}
                            onClick={(event: any) => {
                                if (event.points && event.points.length > 0) {
                                    const point = event.points[0];
                                    const siteId =
                                        point.text ||
                                        (point.customdata as { site_id?: string })?.site_id ||
                                        (point.data as { text?: string[] })?.text?.[point.pointIndex];
                                    if (siteId) handlePointClick(siteId as string);
                                }
                            }}
                        />
                    </div>

                    {/* Cluster Legend Panel */}
                    <div className="rounded-2xl bg-[#0d1520]/60 border border-white/5 p-5">
                        <h3 className="text-sm font-semibold text-gray-300 mb-4 flex items-center gap-2">
                            <div className="w-1.5 h-1.5 rounded-full bg-cyan-400" />
                            Cluster Legend
                        </h3>
                        <div className="space-y-2">
                            {data?.clusters.map((cluster) => (
                                <div
                                    key={cluster.cluster_id}
                                    className="p-3 rounded-lg border transition-all cursor-pointer"
                                    style={{
                                        backgroundColor:
                                            hoveredCluster === cluster.cluster_id
                                                ? `${cluster.color}20`
                                                : "rgba(255,255,255,0.02)",
                                        borderColor:
                                            hoveredCluster === cluster.cluster_id
                                                ? `${cluster.color}50`
                                                : "rgba(255,255,255,0.05)",
                                    }}
                                    onMouseEnter={() => setHoveredCluster(cluster.cluster_id)}
                                    onMouseLeave={() => setHoveredCluster(null)}
                                >
                                    <div className="flex items-center justify-between">
                                        <div className="flex items-center gap-2.5">
                                            <div
                                                className="w-3 h-3 rounded-full shadow-sm"
                                                style={{
                                                    backgroundColor: cluster.color,
                                                    boxShadow: `0 0 8px ${cluster.color}60`,
                                                }}
                                            />
                                            <span className="text-sm font-medium text-gray-200">
                                                {cluster.name}
                                            </span>
                                        </div>
                                        <span className="text-xs text-gray-500">{cluster.size}</span>
                                    </div>
                                    <div className="flex items-center justify-between mt-1.5 pl-5">
                                        <span className="text-xs text-gray-500">{cluster.description}</span>
                                        <span
                                            className="text-xs px-1.5 py-0.5 rounded"
                                            style={{
                                                backgroundColor:
                                                    cluster.risk_level === "High"
                                                        ? "rgba(239,68,68,0.15)"
                                                        : cluster.risk_level === "Medium"
                                                            ? "rgba(245,158,11,0.15)"
                                                            : "rgba(16,185,129,0.15)",
                                                color:
                                                    cluster.risk_level === "High"
                                                        ? "#f87171"
                                                        : cluster.risk_level === "Medium"
                                                            ? "#fbbf24"
                                                            : "#34d399",
                                            }}
                                        >
                                            {cluster.risk_level}
                                        </span>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>

                {/* Analysis Modal */}
                {showModal && (
                    <div
                        className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm"
                        onClick={closeModal}
                    >
                        <div
                            className="bg-[#0d1520] rounded-2xl border border-white/10 shadow-2xl w-full max-w-2xl max-h-[85vh] overflow-hidden"
                            onClick={(e) => e.stopPropagation()}
                        >
                            {/* Modal Header */}
                            <div className="p-5 border-b border-white/10 flex items-center justify-between">
                                <div className="flex items-center gap-4">
                                    <div
                                        className="w-11 h-11 rounded-xl flex items-center justify-center"
                                        style={{
                                            backgroundColor: analysis?.cluster_color?.primary
                                                ? `${analysis.cluster_color.primary}20`
                                                : "rgba(6,182,212,0.15)",
                                        }}
                                    >
                                        <Brain
                                            className="w-5 h-5"
                                            style={{
                                                color: analysis?.cluster_color?.primary || "#06b6d4",
                                            }}
                                        />
                                    </div>
                                    <div>
                                        <h2 className="text-lg font-semibold text-white">{selectedSite}</h2>
                                        <p className="text-sm text-gray-500">AI-Powered Analysis</p>
                                    </div>
                                </div>
                                <div className="flex items-center gap-3">
                                    {analysis?.risk_level && (
                                        <span
                                            className="px-3 py-1 rounded-full text-xs font-medium"
                                            style={{
                                                backgroundColor: analysis.risk_color?.bg || "rgba(16,185,129,0.15)",
                                                color: analysis.risk_color?.text || "#10b981",
                                            }}
                                        >
                                            {analysis.risk_level} Risk
                                        </span>
                                    )}
                                    <button
                                        onClick={closeModal}
                                        className="w-8 h-8 rounded-lg bg-white/5 hover:bg-white/10 flex items-center justify-center text-gray-400 hover:text-white transition-colors"
                                    >
                                        <X className="w-4 h-4" />
                                    </button>
                                </div>
                            </div>

                            {/* Modal Content */}
                            <div className="p-5 overflow-y-auto max-h-[calc(85vh-80px)]">
                                {analyzingLoading ? (
                                    <div className="text-center py-16">
                                        <div className="relative w-14 h-14 mx-auto mb-5">
                                            <div className="absolute inset-0 rounded-full border-4 border-violet-500/20" />
                                            <div className="absolute inset-0 rounded-full border-4 border-transparent border-t-violet-500 animate-spin" />
                                            <Brain className="absolute inset-0 m-auto w-5 h-5 text-violet-400" />
                                        </div>
                                        <p className="text-gray-300 font-medium">Analyzing {selectedSite}</p>
                                        <p className="text-gray-500 text-sm mt-1">
                                            AI is evaluating site performance...
                                        </p>
                                    </div>
                                ) : analysis ? (
                                    <div className="space-y-4">
                                        {/* Summary */}
                                        <div className="p-4 rounded-xl bg-white/[0.02] border border-white/5">
                                            <div className="flex items-center gap-2 mb-2">
                                                <Info className="w-4 h-4 text-gray-400" />
                                                <h3 className="text-sm font-medium text-gray-300">Summary</h3>
                                            </div>
                                            <p className="text-gray-400 text-sm leading-relaxed">
                                                {analysis.summary}
                                            </p>
                                        </div>

                                        <div className="grid grid-cols-2 gap-4">
                                            {/* Strengths */}
                                            {analysis.strengths && analysis.strengths.length > 0 && (
                                                <div className="p-4 rounded-xl bg-emerald-500/5 border border-emerald-500/10">
                                                    <div className="flex items-center gap-2 mb-3">
                                                        <TrendingUp className="w-4 h-4 text-emerald-400" />
                                                        <h3 className="text-sm font-medium text-emerald-400">
                                                            Strengths
                                                        </h3>
                                                    </div>
                                                    <ul className="space-y-2">
                                                        {analysis.strengths.map((s, i) => (
                                                            <li
                                                                key={i}
                                                                className="text-gray-300 text-sm flex items-start gap-2"
                                                            >
                                                                <ChevronRight className="w-3 h-3 text-emerald-500 mt-1 flex-shrink-0" />
                                                                <span>{s}</span>
                                                            </li>
                                                        ))}
                                                    </ul>
                                                </div>
                                            )}

                                            {/* Concerns */}
                                            {analysis.concerns && analysis.concerns.length > 0 && (
                                                <div className="p-4 rounded-xl bg-amber-500/5 border border-amber-500/10">
                                                    <div className="flex items-center gap-2 mb-3">
                                                        <AlertCircle className="w-4 h-4 text-amber-400" />
                                                        <h3 className="text-sm font-medium text-amber-400">Concerns</h3>
                                                    </div>
                                                    <ul className="space-y-2">
                                                        {analysis.concerns.map((c, i) => (
                                                            <li
                                                                key={i}
                                                                className="text-gray-300 text-sm flex items-start gap-2"
                                                            >
                                                                <ChevronRight className="w-3 h-3 text-amber-500 mt-1 flex-shrink-0" />
                                                                <span>{c}</span>
                                                            </li>
                                                        ))}
                                                    </ul>
                                                </div>
                                            )}
                                        </div>

                                        {/* Recommendations */}
                                        {analysis.recommendations && analysis.recommendations.length > 0 && (
                                            <div className="p-4 rounded-xl bg-blue-500/5 border border-blue-500/10">
                                                <div className="flex items-center gap-2 mb-3">
                                                    <Lightbulb className="w-4 h-4 text-blue-400" />
                                                    <h3 className="text-sm font-medium text-blue-400">
                                                        Recommendations
                                                    </h3>
                                                </div>
                                                <div className="space-y-2">
                                                    {analysis.recommendations.map((r, i) => (
                                                        <div
                                                            key={i}
                                                            className="p-3 rounded-lg bg-white/[0.02] border border-white/5"
                                                        >
                                                            {typeof r === "string" ? (
                                                                <span className="text-gray-300 text-sm">{r}</span>
                                                            ) : (
                                                                <>
                                                                    <div className="flex items-center gap-2 mb-1">
                                                                        <span
                                                                            className={`px-1.5 py-0.5 rounded text-xs font-medium ${r.priority === "High"
                                                                                ? "bg-red-500/15 text-red-400"
                                                                                : r.priority === "Medium"
                                                                                    ? "bg-amber-500/15 text-amber-400"
                                                                                    : "bg-emerald-500/15 text-emerald-400"
                                                                                }`}
                                                                        >
                                                                            {r.priority}
                                                                        </span>
                                                                        <span className="font-medium text-gray-200 text-sm">
                                                                            {r.action}
                                                                        </span>
                                                                    </div>
                                                                    <p className="text-gray-500 text-xs pl-0">
                                                                        {r.rationale}
                                                                    </p>
                                                                </>
                                                            )}
                                                        </div>
                                                    ))}
                                                </div>
                                            </div>
                                        )}

                                        {/* Cluster Context */}
                                        {analysis.cluster_context && (
                                            <div
                                                className="p-4 rounded-xl border"
                                                style={{
                                                    backgroundColor: analysis.cluster_color?.primary
                                                        ? `${analysis.cluster_color.primary}08`
                                                        : "rgba(139,92,246,0.05)",
                                                    borderColor: analysis.cluster_color?.primary
                                                        ? `${analysis.cluster_color.primary}20`
                                                        : "rgba(139,92,246,0.1)",
                                                }}
                                            >
                                                <div className="flex items-center gap-2 mb-2">
                                                    <Layers
                                                        className="w-4 h-4"
                                                        style={{
                                                            color: analysis.cluster_color?.primary || "#8b5cf6",
                                                        }}
                                                    />
                                                    <h3
                                                        className="text-sm font-medium"
                                                        style={{
                                                            color: analysis.cluster_color?.primary || "#8b5cf6",
                                                        }}
                                                    >
                                                        Cluster Context
                                                    </h3>
                                                </div>
                                                <p className="text-gray-400 text-sm">{analysis.cluster_context}</p>
                                            </div>
                                        )}
                                    </div>
                                ) : null}
                            </div>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}
