import { useState, useEffect } from 'react';
import {
    PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, ResponsiveContainer,
    RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Tooltip,
    AreaChart, Area, Legend, CartesianGrid, ComposedChart, Line
} from 'recharts';
import {
    TrendingUp, TrendingDown, Activity, Users, Shield, Target,
    AlertTriangle, CheckCircle, BarChart3, Loader2, RefreshCw,
    Sparkles, Zap, Award, Clock
} from 'lucide-react';

// Mock data
const dqiData = [
    { name: 'Grade A', value: 45, color: '#10b981', label: 'Excellent' },
    { name: 'Grade B', value: 78, color: '#3b82f6', label: 'Good' },
    { name: 'Grade C', value: 52, color: '#f59e0b', label: 'Average' },
    { name: 'Grade D', value: 23, color: '#f97316', label: 'Below Avg' },
    { name: 'Grade F', value: 8, color: '#ef4444', label: 'Critical' },
];

const riskData = [
    { name: 'Low', value: 120, color: '#22c55e' },
    { name: 'Medium', value: 56, color: '#eab308' },
    { name: 'High', value: 24, color: '#f97316' },
    { name: 'Critical', value: 6, color: '#dc2626' },
];

const trendData = [
    { month: 'Jan', dqi: 72, enrollment: 78, queries: 85 },
    { month: 'Feb', dqi: 74, enrollment: 82, queries: 82 },
    { month: 'Mar', dqi: 76, enrollment: 85, queries: 88 },
    { month: 'Apr', dqi: 75, enrollment: 83, queries: 86 },
    { month: 'May', dqi: 78, enrollment: 88, queries: 90 },
    { month: 'Jun', dqi: 82, enrollment: 92, queries: 94 },
];

const topSites = [
    { site: 'Site 0042', score: 96.5 },
    { site: 'Site 0127', score: 94.2 },
    { site: 'Site 0089', score: 92.8 },
    { site: 'Site 0156', score: 91.3 },
    { site: 'Site 0203', score: 89.7 },
];

const bottomSites = [
    { site: 'Site 1234', score: 45.2 },
    { site: 'Site 0987', score: 48.5 },
    { site: 'Site 0654', score: 52.1 },
    { site: 'Site 0321', score: 55.8 },
    { site: 'Site 0789', score: 58.3 },
];

const radarData = [
    { metric: 'Data Quality', value: 85 },
    { metric: 'Enrollment', value: 78 },
    { metric: 'Query Speed', value: 92 },
    { metric: 'Protocol', value: 88 },
    { metric: 'Timeliness', value: 72 },
    { metric: 'Completeness', value: 90 },
];

const issuesData = [
    { category: 'Missing Data', count: 234, color: '#ef4444' },
    { category: 'Late Submissions', count: 189, color: '#f97316' },
    { category: 'Query Delays', count: 156, color: '#eab308' },
    { category: 'Protocol Issues', count: 98, color: '#8b5cf6' },
    { category: 'Enrollment Gaps', count: 67, color: '#3b82f6' },
];

// Custom Tooltip
const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
        return (
            <div className="bg-white/95 backdrop-blur-sm p-3 rounded-xl shadow-xl border border-gray-100">
                <p className="font-semibold text-gray-800 text-sm">{label || payload[0].name}</p>
                {payload.map((entry: any, index: number) => (
                    <p key={index} className="text-sm" style={{ color: entry.color }}>
                        {entry.name || entry.dataKey}: <span className="font-bold">{entry.value}</span>
                    </p>
                ))}
            </div>
        );
    }
    return null;
};

// Animated Number Component
const AnimatedNumber = ({ value, suffix = '' }: { value: number | string; suffix?: string }) => {
    return (
        <span className="tabular-nums">{value}{suffix}</span>
    );
};

export function ExecutiveDashboard() {
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const timer = setTimeout(() => setLoading(false), 800);
        return () => clearTimeout(timer);
    }, []);

    if (loading) {
        return (
            <div className="flex items-center justify-center h-[80vh]">
                <div className="text-center">
                    <div className="relative w-20 h-20 mx-auto mb-6">
                        <div className="absolute inset-0 rounded-full border-4 border-blue-200"></div>
                        <div className="absolute inset-0 rounded-full border-4 border-transparent border-t-blue-600 animate-spin"></div>
                        <Sparkles className="absolute inset-0 m-auto w-8 h-8 text-blue-600" />
                    </div>
                    <p className="text-gray-600 text-lg font-medium">Loading Dashboard...</p>
                </div>
            </div>
        );
    }

    const totalSites = dqiData.reduce((sum, d) => sum + d.value, 0);

    return (
        <div className="space-y-5 pb-8">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-3xl font-bold bg-gradient-to-r from-blue-600 via-purple-600 to-pink-600 bg-clip-text text-transparent">
                        Executive Dashboard
                    </h1>
                    <p className="text-gray-500 text-sm mt-1 flex items-center gap-2">
                        <Clock className="w-4 h-4" />
                        Real-time Portfolio Overview
                    </p>
                </div>
                <button className="px-5 py-2.5 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-xl hover:shadow-xl hover:shadow-blue-500/25 transition-all flex items-center gap-2 font-medium">
                    <RefreshCw className="w-4 h-4" />
                    Refresh
                </button>
            </div>

            {/* KPI Cards */}
            <div className="grid grid-cols-4 gap-4">
                <div className="relative overflow-hidden bg-gradient-to-br from-blue-500 to-blue-600 rounded-2xl p-5 text-white shadow-xl shadow-blue-500/20">
                    <div className="absolute -right-4 -top-4 w-24 h-24 bg-white/10 rounded-full blur-2xl"></div>
                    <div className="relative">
                        <div className="flex items-center justify-between mb-3">
                            <BarChart3 className="w-8 h-8 opacity-80" />
                            <span className="flex items-center gap-1 text-sm bg-white/20 px-2 py-1 rounded-full">
                                <TrendingUp className="w-3 h-3" /> +12%
                            </span>
                        </div>
                        <div className="text-4xl font-bold mb-1"><AnimatedNumber value={206} /></div>
                        <div className="text-blue-100 text-sm font-medium">Active Sites</div>
                    </div>
                </div>

                <div className="relative overflow-hidden bg-gradient-to-br from-purple-500 to-purple-600 rounded-2xl p-5 text-white shadow-xl shadow-purple-500/20">
                    <div className="absolute -right-4 -top-4 w-24 h-24 bg-white/10 rounded-full blur-2xl"></div>
                    <div className="relative">
                        <div className="flex items-center justify-between mb-3">
                            <Users className="w-8 h-8 opacity-80" />
                            <span className="flex items-center gap-1 text-sm bg-white/20 px-2 py-1 rounded-full">
                                <TrendingUp className="w-3 h-3" /> +8%
                            </span>
                        </div>
                        <div className="text-4xl font-bold mb-1"><AnimatedNumber value="12,847" /></div>
                        <div className="text-purple-100 text-sm font-medium">Total Subjects</div>
                    </div>
                </div>

                <div className="relative overflow-hidden bg-gradient-to-br from-emerald-500 to-emerald-600 rounded-2xl p-5 text-white shadow-xl shadow-emerald-500/20">
                    <div className="absolute -right-4 -top-4 w-24 h-24 bg-white/10 rounded-full blur-2xl"></div>
                    <div className="relative">
                        <div className="flex items-center justify-between mb-3">
                            <Target className="w-8 h-8 opacity-80" />
                            <span className="flex items-center gap-1 text-sm bg-white/20 px-2 py-1 rounded-full">
                                <TrendingUp className="w-3 h-3" /> +5.2
                            </span>
                        </div>
                        <div className="text-4xl font-bold mb-1"><AnimatedNumber value={78.4} /></div>
                        <div className="text-emerald-100 text-sm font-medium">Average DQI</div>
                    </div>
                </div>

                <div className="relative overflow-hidden bg-gradient-to-br from-orange-500 to-orange-600 rounded-2xl p-5 text-white shadow-xl shadow-orange-500/20">
                    <div className="absolute -right-4 -top-4 w-24 h-24 bg-white/10 rounded-full blur-2xl"></div>
                    <div className="relative">
                        <div className="flex items-center justify-between mb-3">
                            <Activity className="w-8 h-8 opacity-80" />
                            <span className="flex items-center gap-1 text-sm bg-white/20 px-2 py-1 rounded-full">
                                <Zap className="w-3 h-3" /> Active
                            </span>
                        </div>
                        <div className="text-4xl font-bold mb-1"><AnimatedNumber value={24} /></div>
                        <div className="text-orange-100 text-sm font-medium">Active Studies</div>
                    </div>
                </div>
            </div>

            {/* Main Charts Row */}
            <div className="grid grid-cols-3 gap-4">
                {/* DQI Distribution - Larger Pie */}
                <div className="bg-white rounded-2xl p-5 shadow-lg shadow-gray-200/50 border border-gray-100">
                    <h3 className="text-base font-semibold text-gray-800 mb-2 flex items-center gap-2">
                        <div className="w-2 h-2 rounded-full bg-blue-500"></div>
                        DQI Grade Distribution
                    </h3>
                    <div className="h-[200px]">
                        <ResponsiveContainer width="100%" height="100%">
                            <PieChart>
                                <Pie
                                    data={dqiData}
                                    cx="50%"
                                    cy="50%"
                                    innerRadius={50}
                                    outerRadius={80}
                                    paddingAngle={2}
                                    dataKey="value"
                                >
                                    {dqiData.map((entry, index) => (
                                        <Cell key={`cell-${index}`} fill={entry.color} stroke="white" strokeWidth={2} />
                                    ))}
                                </Pie>
                                <Tooltip content={<CustomTooltip />} />
                            </PieChart>
                        </ResponsiveContainer>
                    </div>
                    <div className="flex flex-wrap justify-center gap-3 mt-2">
                        {dqiData.map((item) => (
                            <div key={item.name} className="flex items-center gap-1.5 text-xs">
                                <div className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: item.color }} />
                                <span className="text-gray-600">{item.name.split(' ')[1]}: {item.value}</span>
                            </div>
                        ))}
                    </div>
                </div>

                {/* Risk Distribution */}
                <div className="bg-white rounded-2xl p-5 shadow-lg shadow-gray-200/50 border border-gray-100">
                    <h3 className="text-base font-semibold text-gray-800 mb-2 flex items-center gap-2">
                        <div className="w-2 h-2 rounded-full bg-orange-500"></div>
                        Risk Distribution
                    </h3>
                    <div className="h-[200px]">
                        <ResponsiveContainer width="100%" height="100%">
                            <PieChart>
                                <Pie
                                    data={riskData}
                                    cx="50%"
                                    cy="50%"
                                    innerRadius={50}
                                    outerRadius={80}
                                    paddingAngle={2}
                                    dataKey="value"
                                >
                                    {riskData.map((entry, index) => (
                                        <Cell key={`cell-${index}`} fill={entry.color} stroke="white" strokeWidth={2} />
                                    ))}
                                </Pie>
                                <Tooltip content={<CustomTooltip />} />
                            </PieChart>
                        </ResponsiveContainer>
                    </div>
                    <div className="flex justify-center gap-4 mt-2">
                        {riskData.map((item) => (
                            <div key={item.name} className="flex items-center gap-1.5 text-xs">
                                <div className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: item.color }} />
                                <span className="text-gray-600">{item.name}: {item.value}</span>
                            </div>
                        ))}
                    </div>
                </div>

                {/* Quality Radar */}
                <div className="bg-white rounded-2xl p-5 shadow-lg shadow-gray-200/50 border border-gray-100">
                    <h3 className="text-base font-semibold text-gray-800 mb-2 flex items-center gap-2">
                        <div className="w-2 h-2 rounded-full bg-purple-500"></div>
                        Quality Metrics
                    </h3>
                    <div className="h-[200px]">
                        <ResponsiveContainer width="100%" height="100%">
                            <RadarChart cx="50%" cy="50%" outerRadius="70%" data={radarData}>
                                <PolarGrid stroke="#e5e7eb" />
                                <PolarAngleAxis dataKey="metric" tick={{ fill: '#6b7280', fontSize: 10 }} />
                                <PolarRadiusAxis angle={30} domain={[0, 100]} tick={false} axisLine={false} />
                                <Radar name="Score" dataKey="value" stroke="#8b5cf6" fill="#8b5cf6" fillOpacity={0.4} strokeWidth={2} />
                                <Tooltip content={<CustomTooltip />} />
                            </RadarChart>
                        </ResponsiveContainer>
                    </div>
                </div>
            </div>

            {/* Performance Trends - Full Width */}
            <div className="bg-white rounded-2xl p-5 shadow-lg shadow-gray-200/50 border border-gray-100">
                <h3 className="text-base font-semibold text-gray-800 mb-4 flex items-center gap-2">
                    <TrendingUp className="w-5 h-5 text-green-500" />
                    Performance Trends (6 Months)
                </h3>
                <div className="h-[250px]">
                    <ResponsiveContainer width="100%" height="100%">
                        <ComposedChart data={trendData}>
                            <defs>
                                <linearGradient id="dqiGradient" x1="0" y1="0" x2="0" y2="1">
                                    <stop offset="0%" stopColor="#3b82f6" stopOpacity={0.3} />
                                    <stop offset="100%" stopColor="#3b82f6" stopOpacity={0.05} />
                                </linearGradient>
                                <linearGradient id="enrollGradient" x1="0" y1="0" x2="0" y2="1">
                                    <stop offset="0%" stopColor="#10b981" stopOpacity={0.3} />
                                    <stop offset="100%" stopColor="#10b981" stopOpacity={0.05} />
                                </linearGradient>
                            </defs>
                            <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" vertical={false} />
                            <XAxis dataKey="month" stroke="#9ca3af" fontSize={12} tickLine={false} axisLine={false} />
                            <YAxis stroke="#9ca3af" fontSize={12} tickLine={false} axisLine={false} domain={[60, 100]} />
                            <Tooltip content={<CustomTooltip />} />
                            <Legend wrapperStyle={{ paddingTop: 10 }} />
                            <Area type="monotone" dataKey="dqi" name="DQI Score" stroke="#3b82f6" fill="url(#dqiGradient)" strokeWidth={3} dot={{ fill: '#3b82f6', strokeWidth: 2, r: 4 }} />
                            <Area type="monotone" dataKey="enrollment" name="Enrollment Rate" stroke="#10b981" fill="url(#enrollGradient)" strokeWidth={3} dot={{ fill: '#10b981', strokeWidth: 2, r: 4 }} />
                            <Line type="monotone" dataKey="queries" name="Query Resolution" stroke="#f59e0b" strokeWidth={2} dot={{ fill: '#f59e0b', r: 3 }} strokeDasharray="5 5" />
                        </ComposedChart>
                    </ResponsiveContainer>
                </div>
            </div>

            {/* Site Rankings Row */}
            <div className="grid grid-cols-2 gap-4">
                {/* Top Sites */}
                <div className="bg-white rounded-2xl p-5 shadow-lg shadow-gray-200/50 border border-gray-100">
                    <h3 className="text-base font-semibold text-gray-800 mb-4 flex items-center gap-2">
                        <Award className="w-5 h-5 text-green-500" />
                        Top Performing Sites
                    </h3>
                    <div className="h-[180px]">
                        <ResponsiveContainer width="100%" height="100%">
                            <BarChart data={topSites} layout="vertical" margin={{ left: 10, right: 20 }}>
                                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" horizontal={true} vertical={false} />
                                <XAxis type="number" domain={[0, 100]} stroke="#9ca3af" fontSize={11} tickLine={false} axisLine={false} />
                                <YAxis dataKey="site" type="category" width={80} stroke="#6b7280" fontSize={11} tickLine={false} axisLine={false} style={{ whiteSpace: 'nowrap' }} />
                                <Tooltip content={<CustomTooltip />} />
                                <Bar dataKey="score" radius={[0, 6, 6, 0]} barSize={20}>
                                    {topSites.map((_, index) => (
                                        <Cell key={`cell-${index}`} fill={`url(#greenGradient)`} />
                                    ))}
                                </Bar>
                                <defs>
                                    <linearGradient id="greenGradient" x1="0" y1="0" x2="1" y2="0">
                                        <stop offset="0%" stopColor="#22c55e" />
                                        <stop offset="100%" stopColor="#10b981" />
                                    </linearGradient>
                                </defs>
                            </BarChart>
                        </ResponsiveContainer>
                    </div>
                </div>

                {/* Bottom Sites */}
                <div className="bg-white rounded-2xl p-5 shadow-lg shadow-gray-200/50 border border-gray-100">
                    <h3 className="text-base font-semibold text-gray-800 mb-4 flex items-center gap-2">
                        <AlertTriangle className="w-5 h-5 text-red-500" />
                        Sites Requiring Attention
                    </h3>
                    <div className="h-[180px]">
                        <ResponsiveContainer width="100%" height="100%">
                            <BarChart data={bottomSites} layout="vertical" margin={{ left: 10, right: 20 }}>
                                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" horizontal={true} vertical={false} />
                                <XAxis type="number" domain={[0, 100]} stroke="#9ca3af" fontSize={11} tickLine={false} axisLine={false} />
                                <YAxis dataKey="site" type="category" width={80} stroke="#6b7280" fontSize={11} tickLine={false} axisLine={false} style={{ whiteSpace: 'nowrap' }} />
                                <Tooltip content={<CustomTooltip />} />
                                <Bar dataKey="score" radius={[0, 6, 6, 0]} barSize={20}>
                                    {bottomSites.map((_, index) => (
                                        <Cell key={`cell-${index}`} fill={`url(#redGradient)`} />
                                    ))}
                                </Bar>
                                <defs>
                                    <linearGradient id="redGradient" x1="0" y1="0" x2="1" y2="0">
                                        <stop offset="0%" stopColor="#ef4444" />
                                        <stop offset="100%" stopColor="#f97316" />
                                    </linearGradient>
                                </defs>
                            </BarChart>
                        </ResponsiveContainer>
                    </div>
                </div>
            </div>

            {/* Issues by Category */}
            <div className="bg-white rounded-2xl p-5 shadow-lg shadow-gray-200/50 border border-gray-100">
                <h3 className="text-base font-semibold text-gray-800 mb-4 flex items-center gap-2">
                    <AlertTriangle className="w-5 h-5 text-amber-500" />
                    Issues by Category
                </h3>
                <div className="h-[160px]">
                    <ResponsiveContainer width="100%" height="100%">
                        <BarChart data={issuesData} margin={{ left: 0, right: 0, bottom: 0 }}>
                            <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" vertical={false} />
                            <XAxis dataKey="category" stroke="#9ca3af" fontSize={10} tickLine={false} axisLine={false} />
                            <YAxis stroke="#9ca3af" fontSize={11} tickLine={false} axisLine={false} />
                            <Tooltip content={<CustomTooltip />} />
                            <Bar dataKey="count" radius={[6, 6, 0, 0]} barSize={50}>
                                {issuesData.map((entry, index) => (
                                    <Cell key={`cell-${index}`} fill={entry.color} />
                                ))}
                            </Bar>
                        </BarChart>
                    </ResponsiveContainer>
                </div>
            </div>

            {/* Stats Footer */}
            <div className="grid grid-cols-4 gap-4">
                <div className="bg-gradient-to-br from-green-50 to-emerald-50 rounded-2xl p-5 border border-green-100 text-center">
                    <div className="text-3xl font-bold text-green-600">{dqiData[0].value + dqiData[1].value}</div>
                    <div className="text-sm text-green-700 font-medium mt-1">High Quality Sites</div>
                    <div className="text-xs text-green-600 mt-0.5">Grade A & B</div>
                </div>
                <div className="bg-gradient-to-br from-red-50 to-orange-50 rounded-2xl p-5 border border-red-100 text-center">
                    <div className="text-3xl font-bold text-red-600">{riskData[2].value + riskData[3].value}</div>
                    <div className="text-sm text-red-700 font-medium mt-1">At Risk Sites</div>
                    <div className="text-xs text-red-600 mt-0.5">High & Critical</div>
                </div>
                <div className="bg-gradient-to-br from-blue-50 to-indigo-50 rounded-2xl p-5 border border-blue-100 text-center">
                    <div className="text-3xl font-bold text-blue-600">92%</div>
                    <div className="text-sm text-blue-700 font-medium mt-1">Query Resolution</div>
                    <div className="text-xs text-blue-600 mt-0.5">Above Target</div>
                </div>
                <div className="bg-gradient-to-br from-purple-50 to-pink-50 rounded-2xl p-5 border border-purple-100 text-center">
                    <div className="text-3xl font-bold text-purple-600">88%</div>
                    <div className="text-sm text-purple-700 font-medium mt-1">Protocol Adherence</div>
                    <div className="text-xs text-purple-600 mt-0.5">Excellent</div>
                </div>
            </div>
        </div>
    );
}
