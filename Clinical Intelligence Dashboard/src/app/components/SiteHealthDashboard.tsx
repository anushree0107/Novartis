import { useState } from 'react';
import {
    PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, ResponsiveContainer,
    RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Tooltip
} from 'recharts';
import { ChevronDown, Loader2, AlertTriangle, Shield, Users, TrendingUp, Activity, Target } from 'lucide-react';
import {
    fetchDQI,
    fetchSiteRisk,
    fetchSiteCluster,
    DQIResponse,
    SiteRiskDetail,
    SiteCluster
} from '../services/api';

interface SiteHealthDashboardProps {
    onAiClick: (title: string, content: string) => void;
}

interface SiteHealthData {
    dqi: DQIResponse | null;
    risk: SiteRiskDetail | null;
    cluster: SiteCluster | null;
}

export function SiteHealthDashboard({ onAiClick }: SiteHealthDashboardProps) {
    const [siteId, setSiteId] = useState('');
    const [data, setData] = useState<SiteHealthData>({ dqi: null, risk: null, cluster: null });
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [activeTab, setActiveTab] = useState<'overview' | 'dqi' | 'risk' | 'cluster'>('overview');

    const fetchAllData = async () => {
        if (!siteId.trim()) {
            setError('Please enter a Site ID');
            return;
        }

        setLoading(true);
        setError(null);

        try {
            // Fetch all three data sources in parallel
            const [dqiRes, riskRes, clusterRes] = await Promise.allSettled([
                fetchDQI('site', siteId),
                fetchSiteRisk(siteId),
                fetchSiteCluster(siteId)
            ]);

            setData({
                dqi: dqiRes.status === 'fulfilled' ? dqiRes.value : null,
                risk: riskRes.status === 'fulfilled' ? riskRes.value : null,
                cluster: clusterRes.status === 'fulfilled' ? clusterRes.value : null
            });

            // Check if at least one succeeded
            if (dqiRes.status === 'rejected' && riskRes.status === 'rejected' && clusterRes.status === 'rejected') {
                setError('Could not fetch any data for this site. Make sure the backend is running.');
            }
        } catch (err: any) {
            setError(err.message || 'Failed to fetch site data');
        } finally {
            setLoading(false);
        }
    };

    const getGradeColor = (grade: string) => {
        const colors: Record<string, string> = {
            A: '#10b981', B: '#0091DF', C: '#f59e0b', D: '#EC6602', F: '#E03C31'
        };
        return colors[grade] || '#888';
    };

    const getRiskColor = (level: string) => {
        const colors: Record<string, string> = {
            Critical: '#DC2626', High: '#F97316', Medium: '#EAB308', Low: '#22C55E'
        };
        return colors[level] || '#888';
    };

    const hasData = data.dqi || data.risk || data.cluster;

    return (
        <div className="space-y-6">
            {/* Header */}
            <div>
                <h2 className="text-2xl font-bold bg-gradient-to-r from-[#EC6602] to-[#0091DF] bg-clip-text text-transparent mb-2">
                    🏥 Site Health Dashboard
                </h2>
                <p className="text-gray-600 text-sm">
                    Unified view of Data Quality, Risk Assessment, and Site Clustering
                </p>
            </div>

            {/* Search Controls */}
            <div className="glass-card p-4 flex flex-wrap gap-4 items-center">
                <div className="flex-1 min-w-[250px]">
                    <input
                        type="text"
                        placeholder="Enter Site ID (e.g., SITE-001)"
                        value={siteId}
                        onChange={(e) => setSiteId(e.target.value)}
                        onKeyDown={(e) => e.key === 'Enter' && fetchAllData()}
                        className="w-full bg-white text-gray-800 px-4 py-3 rounded-lg border-2 border-[#0091DF]/30 focus:border-[#EC6602] focus:outline-none placeholder-gray-500 text-lg"
                    />
                </div>
                <button
                    onClick={fetchAllData}
                    disabled={loading}
                    className="px-8 py-3 bg-gradient-to-r from-[#EC6602] to-[#0091DF] text-white rounded-lg hover:shadow-[0_0_25px_rgba(236,102,2,0.4)] transition-all duration-200 font-semibold text-lg disabled:opacity-50"
                >
                    {loading ? <Loader2 className="w-5 h-5 animate-spin" /> : '🔍 Analyze Site'}
                </button>
            </div>

            {error && (
                <div className="glass-card p-4 border-l-4 border-l-red-500 bg-red-50">
                    <p className="text-red-700">{error}</p>
                </div>
            )}

            {/* Main Dashboard */}
            {hasData && (
                <>
                    {/* KPI Cards Row */}
                    <div className="grid grid-cols-3 gap-6">
                        {/* DQI Score Card */}
                        <div
                            className="glass-card p-6 cursor-pointer hover:shadow-lg transition-all border-t-4"
                            style={{ borderTopColor: data.dqi ? getGradeColor(data.dqi.grade) : '#888' }}
                            onClick={() => setActiveTab('dqi')}
                        >
                            <div className="flex items-center justify-between mb-4">
                                <div className="flex items-center gap-2">
                                    <Target className="w-5 h-5 text-blue-600" />
                                    <span className="text-gray-600 font-medium">Data Quality</span>
                                </div>
                                {data.dqi && (
                                    <span
                                        className="px-3 py-1 rounded-full text-white text-sm font-bold"
                                        style={{ backgroundColor: getGradeColor(data.dqi.grade) }}
                                    >
                                        Grade {data.dqi.grade}
                                    </span>
                                )}
                            </div>
                            <div className="text-center">
                                <div className="text-5xl font-bold" style={{ color: data.dqi ? getGradeColor(data.dqi.grade) : '#888' }}>
                                    {data.dqi ? data.dqi.score.toFixed(1) : '--'}
                                </div>
                                <div className="text-gray-500 text-sm mt-1">/ 100</div>
                            </div>
                            {data.dqi && (
                                <div className="mt-4 text-center">
                                    <span
                                        className={`text-sm px-3 py-1 rounded-full ${data.dqi.is_clean ? 'bg-green-100 text-green-700' : 'bg-yellow-100 text-yellow-700'
                                            }`}
                                    >
                                        {data.dqi.status}
                                    </span>
                                </div>
                            )}
                        </div>

                        {/* Risk Score Card */}
                        <div
                            className="glass-card p-6 cursor-pointer hover:shadow-lg transition-all border-t-4"
                            style={{ borderTopColor: data.risk ? getRiskColor(data.risk.risk_level) : '#888' }}
                            onClick={() => setActiveTab('risk')}
                        >
                            <div className="flex items-center justify-between mb-4">
                                <div className="flex items-center gap-2">
                                    <Shield className="w-5 h-5 text-orange-600" />
                                    <span className="text-gray-600 font-medium">Risk Assessment</span>
                                </div>
                                {data.risk && (
                                    <span
                                        className="px-3 py-1 rounded-full text-white text-sm font-bold"
                                        style={{ backgroundColor: getRiskColor(data.risk.risk_level) }}
                                    >
                                        {data.risk.risk_level}
                                    </span>
                                )}
                            </div>
                            <div className="text-center">
                                <div className="text-5xl font-bold" style={{ color: data.risk ? getRiskColor(data.risk.risk_level) : '#888' }}>
                                    {data.risk ? (data.risk.anomaly_score * 100).toFixed(0) : '--'}
                                </div>
                                <div className="text-gray-500 text-sm mt-1">Anomaly Score</div>
                            </div>
                            {data.risk && (
                                <div className="mt-4 text-center">
                                    <span
                                        className={`text-sm px-3 py-1 rounded-full ${data.risk.is_anomaly ? 'bg-red-100 text-red-700' : 'bg-green-100 text-green-700'
                                            }`}
                                    >
                                        {data.risk.is_anomaly ? '⚠️ Anomaly Detected' : '✅ Normal'}
                                    </span>
                                </div>
                            )}
                        </div>

                        {/* Cluster Card */}
                        <div
                            className="glass-card p-6 cursor-pointer hover:shadow-lg transition-all border-t-4"
                            style={{ borderTopColor: data.cluster?.cluster_color?.primary || '#888' }}
                            onClick={() => setActiveTab('cluster')}
                        >
                            <div className="flex items-center justify-between mb-4">
                                <div className="flex items-center gap-2">
                                    <Users className="w-5 h-5 text-purple-600" />
                                    <span className="text-gray-600 font-medium">Site Segment</span>
                                </div>
                                {data.cluster && (
                                    <span
                                        className="px-3 py-1 rounded-full text-white text-sm font-bold"
                                        style={{ backgroundColor: data.cluster.cluster_color?.primary || '#6366F1' }}
                                    >
                                        {data.cluster.cluster_name}
                                    </span>
                                )}
                            </div>
                            <div className="text-center">
                                <div
                                    className="text-5xl font-bold"
                                    style={{ color: data.cluster?.cluster_color?.primary || '#888' }}
                                >
                                    {data.cluster ? `#${data.cluster.cluster_id}` : '--'}
                                </div>
                                <div className="text-gray-500 text-sm mt-1">Cluster Group</div>
                            </div>
                            {data.cluster && (
                                <div className="mt-4 text-center">
                                    <span
                                        className="text-sm px-3 py-1 rounded-full"
                                        style={{
                                            backgroundColor: getRiskColor(data.cluster.risk_level) + '20',
                                            color: getRiskColor(data.cluster.risk_level)
                                        }}
                                    >
                                        {data.cluster.risk_level} Risk Segment
                                    </span>
                                </div>
                            )}
                        </div>
                    </div>

                    {/* Tab Navigation */}
                    <div className="flex gap-2 border-b border-gray-200">
                        {['overview', 'dqi', 'risk', 'cluster'].map((tab) => (
                            <button
                                key={tab}
                                onClick={() => setActiveTab(tab as any)}
                                className={`px-6 py-3 font-medium transition-all ${activeTab === tab
                                        ? 'text-[#EC6602] border-b-2 border-[#EC6602]'
                                        : 'text-gray-500 hover:text-gray-700'
                                    }`}
                            >
                                {tab === 'overview' && '📊 Overview'}
                                {tab === 'dqi' && '📋 DQI Details'}
                                {tab === 'risk' && '⚠️ Risk Factors'}
                                {tab === 'cluster' && '👥 Cluster Info'}
                            </button>
                        ))}
                    </div>

                    {/* Tab Content */}
                    <div className="grid grid-cols-2 gap-6">
                        {/* Overview Tab */}
                        {activeTab === 'overview' && (
                            <>
                                {/* Combined Recommendations */}
                                <div className="glass-card p-6 col-span-2">
                                    <h3 className="text-lg font-semibold text-gray-800 mb-4 flex items-center gap-2">
                                        <TrendingUp className="w-5 h-5 text-green-600" />
                                        Actionable Recommendations
                                    </h3>
                                    <div className="grid grid-cols-2 gap-4">
                                        {/* From DQI */}
                                        {data.dqi?.recommendations?.map((rec, idx) => (
                                            <div key={`dqi-${idx}`} className="flex items-start gap-3 p-3 bg-blue-50 rounded-lg">
                                                <span className="text-blue-600 mt-1">📋</span>
                                                <span className="text-gray-700 text-sm">{rec}</span>
                                            </div>
                                        ))}
                                        {/* From Risk */}
                                        {data.risk?.recommendations?.map((rec, idx) => (
                                            <div key={`risk-${idx}`} className="flex items-start gap-3 p-3 bg-orange-50 rounded-lg">
                                                <span className="text-orange-600 mt-1">⚠️</span>
                                                <span className="text-gray-700 text-sm">{rec}</span>
                                            </div>
                                        ))}
                                    </div>
                                </div>

                                {/* Issues */}
                                {data.dqi?.top_issues && data.dqi.top_issues.length > 0 && (
                                    <div className="glass-card p-6">
                                        <h3 className="text-lg font-semibold text-gray-800 mb-4 flex items-center gap-2">
                                            <AlertTriangle className="w-5 h-5 text-red-600" />
                                            Top Issues
                                        </h3>
                                        <ul className="space-y-2">
                                            {data.dqi.top_issues.map((issue, idx) => (
                                                <li key={idx} className="flex items-start gap-2 text-gray-700 text-sm">
                                                    <span className="text-red-500 mt-1">•</span>
                                                    <span>{issue}</span>
                                                </li>
                                            ))}
                                        </ul>
                                    </div>
                                )}

                                {/* Similar Sites */}
                                {(data.cluster?.similar_sites?.length || data.risk?.similar_risk_sites?.length) ? (
                                    <div className="glass-card p-6">
                                        <h3 className="text-lg font-semibold text-gray-800 mb-4 flex items-center gap-2">
                                            <Users className="w-5 h-5 text-purple-600" />
                                            Similar Sites
                                        </h3>
                                        <div className="flex flex-wrap gap-2">
                                            {data.cluster?.similar_sites?.slice(0, 5).map((site, idx) => (
                                                <span
                                                    key={idx}
                                                    className="px-3 py-1 rounded-full text-sm font-medium"
                                                    style={{
                                                        backgroundColor: data.cluster?.cluster_color?.primary + '20',
                                                        color: data.cluster?.cluster_color?.primary
                                                    }}
                                                >
                                                    {site}
                                                </span>
                                            ))}
                                            {data.risk?.similar_risk_sites?.slice(0, 5).map((site, idx) => (
                                                <span
                                                    key={`risk-${idx}`}
                                                    className="px-3 py-1 rounded-full text-sm font-medium"
                                                    style={{
                                                        backgroundColor: getRiskColor(site.risk_level) + '20',
                                                        color: getRiskColor(site.risk_level)
                                                    }}
                                                >
                                                    {site.site_id}
                                                </span>
                                            ))}
                                        </div>
                                    </div>
                                ) : null}
                            </>
                        )}

                        {/* DQI Details Tab */}
                        {activeTab === 'dqi' && data.dqi && (
                            <>
                                <div className="glass-card p-6">
                                    <h3 className="text-lg font-semibold text-gray-800 mb-4">Metric Breakdown</h3>
                                    <div className="space-y-4">
                                        {data.dqi.breakdown.map((item: any, idx: number) => (
                                            <div key={idx}>
                                                <div className="flex justify-between mb-1 text-sm">
                                                    <span className="text-gray-700">{item.metric}</span>
                                                    <span className="text-gray-800 font-medium">
                                                        {typeof item.value === 'number' ? (item.value * 100).toFixed(1) : item.contribution}%
                                                    </span>
                                                </div>
                                                <div className="h-3 bg-gray-200 rounded-full overflow-hidden">
                                                    <div
                                                        className="h-full rounded-full transition-all duration-500"
                                                        style={{
                                                            width: `${Math.min((item.value || item.contribution) * 100, 100)}%`,
                                                            backgroundColor:
                                                                item.status === 'good' || item.status === 'Good'
                                                                    ? '#10b981'
                                                                    : item.status === 'warning' || item.status === 'Warning'
                                                                        ? '#f59e0b'
                                                                        : '#E03C31'
                                                        }}
                                                    />
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                </div>

                                {data.dqi.explanation && (
                                    <div className="glass-card p-6">
                                        <h3 className="text-lg font-semibold text-gray-800 mb-4">AI Explanation</h3>
                                        <p className="text-gray-700 text-sm whitespace-pre-wrap">{data.dqi.explanation}</p>
                                    </div>
                                )}
                            </>
                        )}

                        {/* Risk Factors Tab */}
                        {activeTab === 'risk' && data.risk && (
                            <>
                                <div className="glass-card p-6">
                                    <h3 className="text-lg font-semibold text-gray-800 mb-4">Risk Contributing Factors</h3>
                                    <div className="space-y-3">
                                        {data.risk.feature_contributions_chart?.data?.slice(0, 6).map((item: any, idx: number) => (
                                            <div key={idx}>
                                                <div className="flex justify-between mb-1 text-sm">
                                                    <span className="text-gray-700">{item.name}</span>
                                                    <span className="font-medium" style={{ color: item.color }}>
                                                        {item.formatted_value}
                                                    </span>
                                                </div>
                                                <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
                                                    <div
                                                        className="h-full rounded-full"
                                                        style={{ width: `${item.bar_width}%`, backgroundColor: item.color }}
                                                    />
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                </div>

                                <div className="glass-card p-6">
                                    <h3 className="text-lg font-semibold text-gray-800 mb-4">Control Chart Status</h3>
                                    <div className="space-y-3">
                                        {data.risk.control_charts?.slice(0, 5).map((chart, idx) => (
                                            <div
                                                key={idx}
                                                className="flex items-center justify-between p-3 rounded-lg"
                                                style={{ backgroundColor: chart.is_out_of_control ? '#FEF2F2' : '#F0FDF4' }}
                                            >
                                                <div className="flex items-center gap-2">
                                                    <span>{chart.status_icon}</span>
                                                    <span className="text-gray-700 text-sm">{chart.metric_display_name}</span>
                                                </div>
                                                <span className="font-medium" style={{ color: chart.status_color }}>
                                                    {chart.formatted_value}
                                                </span>
                                            </div>
                                        ))}
                                    </div>
                                </div>

                                {data.risk.explanation && (
                                    <div className="glass-card p-6 col-span-2">
                                        <h3 className="text-lg font-semibold text-gray-800 mb-4">Risk Explanation</h3>
                                        <p className="text-gray-700">{data.risk.explanation}</p>
                                    </div>
                                )}
                            </>
                        )}

                        {/* Cluster Info Tab */}
                        {activeTab === 'cluster' && data.cluster && (
                            <>
                                <div className="glass-card p-6">
                                    <h3 className="text-lg font-semibold text-gray-800 mb-4">Cluster Profile</h3>
                                    <div className="text-center mb-4">
                                        <div
                                            className="inline-block px-6 py-3 rounded-xl text-white font-bold text-lg"
                                            style={{ backgroundColor: data.cluster.cluster_color?.primary || '#6366F1' }}
                                        >
                                            {data.cluster.cluster_name}
                                        </div>
                                    </div>
                                    <p className="text-gray-700 text-center mb-4">{data.cluster.cluster_stats.description}</p>
                                    <div className="flex justify-center gap-4">
                                        <div className="text-center">
                                            <div className="text-2xl font-bold text-gray-800">{data.cluster.cluster_stats.size}</div>
                                            <div className="text-gray-500 text-sm">Sites in Cluster</div>
                                        </div>
                                        {data.cluster.confidence && (
                                            <div className="text-center">
                                                <div className="text-2xl font-bold text-gray-800">{data.cluster.confidence.toFixed(0)}%</div>
                                                <div className="text-gray-500 text-sm">Confidence</div>
                                            </div>
                                        )}
                                    </div>
                                </div>

                                <div className="glass-card p-6">
                                    <h3 className="text-lg font-semibold text-gray-800 mb-4">Cluster Characteristics</h3>
                                    <div className="space-y-3">
                                        {Object.entries(data.cluster.cluster_stats.feature_means || {}).slice(0, 6).map(([key, value], idx) => (
                                            <div key={idx} className="flex justify-between items-center">
                                                <span className="text-gray-600 text-sm">{key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}</span>
                                                <span className="font-medium text-gray-800">
                                                    {typeof value === 'number' ? (value < 1 ? (value * 100).toFixed(1) + '%' : value.toFixed(2)) : value}
                                                </span>
                                            </div>
                                        ))}
                                    </div>
                                </div>

                                {data.cluster.cluster_probabilities && (
                                    <div className="glass-card p-6 col-span-2">
                                        <h3 className="text-lg font-semibold text-gray-800 mb-4">Cluster Membership Probabilities</h3>
                                        <div className="flex gap-3 flex-wrap">
                                            {data.cluster.cluster_probabilities.map((prob, idx) => (
                                                <div
                                                    key={idx}
                                                    className="px-4 py-2 rounded-lg text-white font-medium"
                                                    style={{
                                                        backgroundColor: prob.color,
                                                        opacity: prob.probability / 100 + 0.3
                                                    }}
                                                >
                                                    {prob.cluster_name}: {prob.probability}%
                                                </div>
                                            ))}
                                        </div>
                                    </div>
                                )}
                            </>
                        )}
                    </div>

                    {/* AI Button */}
                    <div className="flex justify-center">
                        <button
                            onClick={() =>
                                onAiClick(
                                    `Site Health Analysis: ${siteId}`,
                                    `**Site Health Summary for ${siteId}**\n\n` +
                                    `**Data Quality Index:** ${data.dqi?.score?.toFixed(1) || 'N/A'}/100 (Grade ${data.dqi?.grade || 'N/A'})\n` +
                                    `**Risk Level:** ${data.risk?.risk_level || 'N/A'} (Score: ${data.risk?.anomaly_score ? (data.risk.anomaly_score * 100).toFixed(0) : 'N/A'})\n` +
                                    `**Cluster:** ${data.cluster?.cluster_name || 'N/A'}\n\n` +
                                    `**Key Issues:**\n${data.dqi?.top_issues?.map((i) => `- ${i}`).join('\n') || 'None identified'}\n\n` +
                                    `**Recommendations:**\n${[...(data.dqi?.recommendations || []), ...(data.risk?.recommendations || [])].map((r) => `- ${r}`).join('\n') || 'None'}`
                                )
                            }
                            className="px-8 py-3 bg-gradient-to-r from-[#EC6602] to-[#0091DF] text-white rounded-xl hover:shadow-[0_0_30px_rgba(236,102,2,0.5)] transition-all duration-200 font-semibold flex items-center gap-2"
                        >
                            🤖 Get AI Analysis
                        </button>
                    </div>
                </>
            )}

            {/* Empty State */}
            {!hasData && !loading && (
                <div className="glass-card p-12 text-center">
                    <div className="text-6xl mb-4">🔍</div>
                    <h3 className="text-xl font-semibold text-gray-700 mb-2">Enter a Site ID to Begin</h3>
                    <p className="text-gray-500">
                        Get a comprehensive health analysis including Data Quality, Risk Assessment, and Site Clustering
                    </p>
                </div>
            )}

            {/* Loading State */}
            {loading && (
                <div className="glass-card p-12 text-center">
                    <Loader2 className="w-12 h-12 animate-spin text-[#EC6602] mx-auto mb-4" />
                    <p className="text-gray-600">Analyzing site health...</p>
                </div>
            )}
        </div>
    );
}
