import React from "react";
import {
    BarChart3,
    TrendingUp,
    TrendingDown,
    Users,
    Building2,
    Activity,
    FlaskConical,
    RefreshCw,
    AlertTriangle,
    Award,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "./ui/card";
import { Badge, Button } from "./ui/badge";
import {
    PieChart,
    Pie,
    Cell,
    ResponsiveContainer,
    LineChart,
    Line,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    Legend,
    BarChart,
    Bar,
    RadarChart,
    PolarGrid,
    PolarAngleAxis,
    PolarRadiusAxis,
    Radar,
} from "recharts";

// KPI Data
const kpiData = [
    {
        title: "Active Sites",
        value: "206",
        change: "+12%",
        trend: "up",
        icon: Building2,
        color: "from-blue-500/20 to-blue-600/10",
        borderColor: "border-blue-500/30",
        iconColor: "text-blue-400",
    },
    {
        title: "Total Subjects",
        value: "12,847",
        change: "+8%",
        trend: "up",
        icon: Users,
        color: "from-cyan-500/20 to-cyan-600/10",
        borderColor: "border-cyan-500/30",
        iconColor: "text-cyan-400",
    },
    {
        title: "Average DQI",
        value: "78.4",
        change: "+5.2",
        trend: "up",
        icon: Activity,
        color: "from-amber-500/20 to-amber-600/10",
        borderColor: "border-amber-500/30",
        iconColor: "text-amber-400",
    },
    {
        title: "Active Studies",
        value: "24",
        change: "-2",
        trend: "down",
        icon: FlaskConical,
        color: "from-emerald-500/20 to-emerald-600/10",
        borderColor: "border-emerald-500/30",
        iconColor: "text-emerald-400",
    },
];

// DQI Grade Distribution
const dqiGradeData = [
    { name: "A", value: 45, color: "#22c55e" },
    { name: "B", value: 78, color: "#3b82f6" },
    { name: "C", value: 52, color: "#f59e0b" },
    { name: "D", value: 23, color: "#f97316" },
    { name: "F", value: 8, color: "#ef4444" },
];

// Risk Distribution
const riskData = [
    { name: "Low", value: 120, color: "#22c55e" },
    { name: "Medium", value: 56, color: "#f59e0b" },
    { name: "High", value: 24, color: "#f97316" },
    { name: "Critical", value: 6, color: "#ef4444" },
];

// Quality Metrics Radar
const qualityMetricsData = [
    { metric: "Data Quality", value: 85 },
    { metric: "Enrollment", value: 72 },
    { metric: "Query Speed", value: 90 },
    { metric: "Protocol", value: 78 },
    { metric: "Timeliness", value: 65 },
    { metric: "Completeness", value: 88 },
];

// Performance Trends
const performanceData = [
    { month: "Jan", dqi: 72, enrollment: 80, queryResolution: 85 },
    { month: "Feb", dqi: 75, enrollment: 78, queryResolution: 88 },
    { month: "Mar", dqi: 78, enrollment: 82, queryResolution: 90 },
    { month: "Apr", dqi: 74, enrollment: 85, queryResolution: 87 },
    { month: "May", dqi: 80, enrollment: 88, queryResolution: 92 },
    { month: "Jun", dqi: 82, enrollment: 90, queryResolution: 95 },
];

// Top Performing Sites
const topSitesData = [
    { site: "Site 0042", score: 96 },
    { site: "Site 0127", score: 94 },
    { site: "Site 0089", score: 91 },
    { site: "Site 0156", score: 88 },
    { site: "Site 0203", score: 85 },
];

// Sites Requiring Attention
const attentionSitesData = [
    { site: "Site 1234", score: 45 },
    { site: "Site 0987", score: 52 },
    { site: "Site 0654", score: 58 },
    { site: "Site 0321", score: 62 },
    { site: "Site 0789", score: 65 },
];

// Issues by Category
const issuesCategoryData = [
    { category: "Data Entry", count: 240, color: "#ef4444" },
    { category: "Protocol", count: 180, color: "#f97316" },
    { category: "Consent", count: 120, color: "#f59e0b" },
    { category: "Lab Values", count: 95, color: "#22c55e" },
    { category: "AE Reporting", count: 75, color: "#3b82f6" },
];

function KPICard({
    data,
}: {
    data: {
        title: string;
        value: string;
        change: string;
        trend: string;
        icon: React.ComponentType<{ className?: string }>;
        color: string;
        borderColor: string;
        iconColor: string;
    };
}) {
    const Icon = data.icon;
    return (
        <Card className={`bg-gradient-to-br ${data.color} border ${data.borderColor} backdrop-blur-sm`}>
            <CardContent className="p-5">
                <div className="flex items-start justify-between">
                    <div className="flex items-center gap-3">
                        <div className={`p-2.5 rounded-lg bg-gray-900/50 ${data.iconColor}`}>
                            <Icon className="h-5 w-5" />
                        </div>
                        <div>
                            <p className="text-sm text-gray-400">{data.title}</p>
                            <p className="text-2xl font-bold text-white">{data.value}</p>
                        </div>
                    </div>
                    <Badge
                        variant="outline"
                        className={`${data.trend === "up"
                                ? "text-emerald-400 border-emerald-400/30 bg-emerald-400/10"
                                : "text-red-400 border-red-400/30 bg-red-400/10"
                            } flex items-center gap-1`}
                    >
                        {data.trend === "up" ? (
                            <TrendingUp className="h-3 w-3" />
                        ) : (
                            <TrendingDown className="h-3 w-3" />
                        )}
                        {data.change}
                    </Badge>
                </div>
            </CardContent>
        </Card>
    );
}

function DonutChart({
    title,
    data,
    icon: Icon,
}: {
    title: string;
    data: { name: string; value: number; color: string }[];
    icon: React.ComponentType<{ className?: string }>;
}) {
    const total = data.reduce((sum, item) => sum + item.value, 0);

    return (
        <Card className="bg-gray-800/30 border-gray-700/50 backdrop-blur-sm">
            <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium flex items-center gap-2">
                    <Icon className="h-4 w-4 text-cyan-400" />
                    {title}
                </CardTitle>
            </CardHeader>
            <CardContent>
                <div className="h-[200px] relative">
                    <ResponsiveContainer width="100%" height="100%">
                        <PieChart>
                            <Pie
                                data={data}
                                cx="50%"
                                cy="50%"
                                innerRadius={55}
                                outerRadius={80}
                                paddingAngle={3}
                                dataKey="value"
                                strokeWidth={0}
                            >
                                {data.map((entry, index) => (
                                    <Cell key={`cell-${index}`} fill={entry.color} />
                                ))}
                            </Pie>
                        </PieChart>
                    </ResponsiveContainer>
                    <div className="absolute inset-0 flex items-center justify-center">
                        <div className="text-center">
                            <p className="text-2xl font-bold text-white">{total}</p>
                            <p className="text-xs text-gray-400">Total</p>
                        </div>
                    </div>
                </div>
                <div className="flex flex-wrap justify-center gap-3 mt-4">
                    {data.map((item, index) => (
                        <div key={index} className="flex items-center gap-1.5 text-xs">
                            <div
                                className="w-2.5 h-2.5 rounded-full"
                                style={{ backgroundColor: item.color }}
                            />
                            <span className="text-gray-400">
                                {item.name}: {item.value}
                            </span>
                        </div>
                    ))}
                </div>
            </CardContent>
        </Card>
    );
}

function QualityMetricsRadar() {
    return (
        <Card className="bg-gray-800/30 border-gray-700/50 backdrop-blur-sm">
            <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium flex items-center gap-2">
                    <Activity className="h-4 w-4 text-cyan-400" />
                    Quality Metrics
                </CardTitle>
            </CardHeader>
            <CardContent>
                <div className="h-[200px]">
                    <ResponsiveContainer width="100%" height="100%">
                        <RadarChart data={qualityMetricsData}>
                            <PolarGrid stroke="rgba(148, 163, 184, 0.2)" />
                            <PolarAngleAxis
                                dataKey="metric"
                                tick={{ fill: "rgba(148, 163, 184, 0.8)", fontSize: 10 }}
                            />
                            <PolarRadiusAxis
                                angle={30}
                                domain={[0, 100]}
                                tick={{ fill: "rgba(148, 163, 184, 0.6)", fontSize: 9 }}
                            />
                            <Radar
                                name="Score"
                                dataKey="value"
                                stroke="rgb(96, 165, 250)"
                                fill="rgba(96, 165, 250, 0.3)"
                                strokeWidth={2}
                            />
                        </RadarChart>
                    </ResponsiveContainer>
                </div>
            </CardContent>
        </Card>
    );
}

function PerformanceTrends() {
    return (
        <Card className="bg-gray-800/30 border-gray-700/50 backdrop-blur-sm col-span-full">
            <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium flex items-center gap-2">
                    <TrendingUp className="h-4 w-4 text-cyan-400" />
                    Performance Trends (6 Months)
                </CardTitle>
            </CardHeader>
            <CardContent>
                <div className="h-[250px]">
                    <ResponsiveContainer width="100%" height="100%">
                        <LineChart data={performanceData}>
                            <CartesianGrid strokeDasharray="3 3" stroke="rgba(148, 163, 184, 0.1)" />
                            <XAxis
                                dataKey="month"
                                tick={{ fill: "rgba(148, 163, 184, 0.8)", fontSize: 11 }}
                                axisLine={{ stroke: "rgba(148, 163, 184, 0.2)" }}
                            />
                            <YAxis
                                domain={[60, 100]}
                                tick={{ fill: "rgba(148, 163, 184, 0.8)", fontSize: 11 }}
                                axisLine={{ stroke: "rgba(148, 163, 184, 0.2)" }}
                            />
                            <Tooltip
                                contentStyle={{
                                    backgroundColor: "rgba(15, 23, 42, 0.95)",
                                    border: "1px solid rgba(148, 163, 184, 0.2)",
                                    borderRadius: "8px",
                                    color: "#fff",
                                }}
                            />
                            <Legend
                                wrapperStyle={{ paddingTop: "20px" }}
                                formatter={(value) => (
                                    <span className="text-xs text-gray-400">{value}</span>
                                )}
                            />
                            <Line
                                type="monotone"
                                dataKey="dqi"
                                name="DQI Score"
                                stroke="#22c55e"
                                strokeWidth={2}
                                dot={{ fill: "#22c55e", strokeWidth: 0, r: 4 }}
                                activeDot={{ r: 6 }}
                            />
                            <Line
                                type="monotone"
                                dataKey="enrollment"
                                name="Enrollment Rate"
                                stroke="#06b6d4"
                                strokeWidth={2}
                                dot={{ fill: "#06b6d4", strokeWidth: 0, r: 4 }}
                                activeDot={{ r: 6 }}
                            />
                            <Line
                                type="monotone"
                                dataKey="queryResolution"
                                name="Query Resolution"
                                stroke="#ec4899"
                                strokeWidth={2}
                                dot={{ fill: "#ec4899", strokeWidth: 0, r: 4 }}
                                activeDot={{ r: 6 }}
                            />
                        </LineChart>
                    </ResponsiveContainer>
                </div>
            </CardContent>
        </Card>
    );
}

function SitePerformanceBar({
    title,
    data,
    icon: Icon,
    variant,
}: {
    title: string;
    data: { site: string; score: number }[];
    icon: React.ComponentType<{ className?: string }>;
    variant: "success" | "danger";
}) {
    const barColor = variant === "success" ? "#22c55e" : "#ef4444";

    return (
        <Card className="bg-gray-800/30 border-gray-700/50 backdrop-blur-sm">
            <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium flex items-center gap-2">
                    <Icon className={`h-4 w-4 ${variant === "success" ? "text-emerald-400" : "text-red-400"}`} />
                    {title}
                </CardTitle>
            </CardHeader>
            <CardContent>
                <div className="h-[200px]">
                    <ResponsiveContainer width="100%" height="100%">
                        <BarChart data={data} layout="vertical" barSize={16}>
                            <CartesianGrid strokeDasharray="3 3" stroke="rgba(148, 163, 184, 0.1)" horizontal={false} />
                            <XAxis
                                type="number"
                                domain={[0, 100]}
                                tick={{ fill: "rgba(148, 163, 184, 0.8)", fontSize: 10 }}
                                axisLine={{ stroke: "rgba(148, 163, 184, 0.2)" }}
                            />
                            <YAxis
                                type="category"
                                dataKey="site"
                                tick={{ fill: "rgba(148, 163, 184, 0.8)", fontSize: 10 }}
                                axisLine={{ stroke: "rgba(148, 163, 184, 0.2)" }}
                                width={65}
                            />
                            <Tooltip
                                contentStyle={{
                                    backgroundColor: "rgba(15, 23, 42, 0.95)",
                                    border: "1px solid rgba(148, 163, 184, 0.2)",
                                    borderRadius: "8px",
                                    color: "#fff",
                                }}
                            />
                            <Bar dataKey="score" fill={barColor} radius={[0, 4, 4, 0]} />
                        </BarChart>
                    </ResponsiveContainer>
                </div>
            </CardContent>
        </Card>
    );
}

function IssuesByCategory() {
    return (
        <Card className="bg-gray-800/30 border-gray-700/50 backdrop-blur-sm col-span-full">
            <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium flex items-center gap-2">
                    <AlertTriangle className="h-4 w-4 text-amber-400" />
                    Issues by Category
                </CardTitle>
            </CardHeader>
            <CardContent>
                <div className="h-[180px]">
                    <ResponsiveContainer width="100%" height="100%">
                        <BarChart data={issuesCategoryData} barSize={40}>
                            <CartesianGrid strokeDasharray="3 3" stroke="rgba(148, 163, 184, 0.1)" vertical={false} />
                            <XAxis
                                dataKey="category"
                                tick={{ fill: "rgba(148, 163, 184, 0.8)", fontSize: 10 }}
                                axisLine={{ stroke: "rgba(148, 163, 184, 0.2)" }}
                            />
                            <YAxis
                                tick={{ fill: "rgba(148, 163, 184, 0.8)", fontSize: 10 }}
                                axisLine={{ stroke: "rgba(148, 163, 184, 0.2)" }}
                            />
                            <Tooltip
                                contentStyle={{
                                    backgroundColor: "rgba(15, 23, 42, 0.95)",
                                    border: "1px solid rgba(148, 163, 184, 0.2)",
                                    borderRadius: "8px",
                                    color: "#fff",
                                }}
                            />
                            <Bar dataKey="count" radius={[4, 4, 0, 0]}>
                                {issuesCategoryData.map((entry, index) => (
                                    <Cell key={`cell-${index}`} fill={entry.color} />
                                ))}
                            </Bar>
                        </BarChart>
                    </ResponsiveContainer>
                </div>
            </CardContent>
        </Card>
    );
}

export function ExecutiveDashboard() {
    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div>
                    <div className="flex items-center gap-3">
                        <h1 className="text-2xl font-bold text-white">Executive Dashboard</h1>
                        <Badge
                            variant="outline"
                            className="bg-emerald-500/10 text-emerald-400 border-emerald-500/30"
                        >
                            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 mr-1.5 animate-pulse" />
                            Live
                        </Badge>
                    </div>
                    <p className="text-sm text-gray-400 mt-1">Real-time Portfolio Overview</p>
                </div>
                <Button variant="outline" size="sm" className="gap-2">
                    <RefreshCw className="h-4 w-4" />
                    Refresh
                </Button>
            </div>

            {/* KPI Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                {kpiData.map((kpi, index) => (
                    <KPICard key={index} data={kpi} />
                ))}
            </div>

            {/* Charts Row 1: Donut Charts + Radar */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                <DonutChart title="DQI Grade Distribution" data={dqiGradeData} icon={BarChart3} />
                <DonutChart title="Risk Distribution" data={riskData} icon={AlertTriangle} />
                <QualityMetricsRadar />
            </div>

            {/* Performance Trends */}
            <PerformanceTrends />

            {/* Site Performance */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <SitePerformanceBar title="Top Performing Sites" data={topSitesData} icon={Award} variant="success" />
                <SitePerformanceBar title="Sites Requiring Attention" data={attentionSitesData} icon={AlertTriangle} variant="danger" />
            </div>

            {/* Issues by Category */}
            <IssuesByCategory />
        </div>
    );
}
