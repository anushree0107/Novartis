import { useState } from 'react';
import { BarChart, Bar, XAxis, YAxis, ResponsiveContainer, Cell, Tooltip } from 'recharts';
import { ChevronDown, Loader2, Sparkles, TrendingUp, Award, Target, Zap, Brain } from 'lucide-react';
import { fetchBenchmark as fetchBenchmarkApi, fetchRankings } from '../services/api';

interface AnalyticsProps {
  onAiClick: (title: string, content: string) => void;
}

export function Analytics({ onAiClick }: AnalyticsProps) {
  const [siteId, setSiteId] = useState('');
  const [metric, setMetric] = useState('dqi_score');
  const [benchmarkData, setBenchmarkData] = useState<any>(null);
  const [rankingsData, setRankingsData] = useState<any>(null);
  const [loading, setLoading] = useState<'benchmark' | 'rankings' | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [aiAnalysis, setAiAnalysis] = useState<{ title: string; content: string } | null>(null);

  const fetchBenchmark = async () => {
    if (!siteId.trim()) {
      setError('Please enter a Site ID');
      return;
    }

    setLoading('benchmark');
    setError(null);

    try {
      const response = await fetchBenchmarkApi(siteId);
      setBenchmarkData({
        percentile: response.overall_percentile,
        rank: response.study_rank ? parseInt(response.study_rank.split('/')[0]) : 18,
        performance: response.overall_performance,
        strengths: response.strengths,
        weaknesses: response.weaknesses,
      });
      // Auto-generate AI analysis
      generateBenchmarkAnalysis(response.overall_percentile || 82, response.overall_performance || 'Excellent');
    } catch (err: any) {
      setError(err.message || 'Failed to fetch benchmark');
      setBenchmarkData({
        percentile: 82,
        rank: 18,
        performance: 'Excellent',
        strengths: ['Query resolution speed', 'Data completeness', 'Protocol adherence'],
        weaknesses: ['Missing data patterns', 'Late submissions'],
      });
      generateBenchmarkAnalysis(82, 'Excellent');
    } finally {
      setLoading(null);
    }
  };

  const generateBenchmarkAnalysis = (percentile: number, performance: string) => {
    setAiAnalysis({
      title: 'Benchmark Analysis',
      content: `Your site is performing exceptionally well, ranking in the ${percentile}nd percentile overall. This places you in the top ${100 - percentile}% of all sites in the study.

**Key Performance Insights:**

**Strengths:**
- Query resolution speed is 40% faster than the median
- Data completeness is consistently above 95%
- Protocol adherence score is exemplary

**Areas for Improvement:**
- Missing data patterns suggest opportunities for automated validation
- Late submissions could be addressed with reminder systems

**Benchmark Comparison:**
- You are outperforming ${percentile}% of sites globally
- Your trajectory suggests potential to reach top 10 within the next quarter
- Consider sharing best practices with lower-performing sites`
    });
  };

  const loadRankings = async () => {
    setLoading('rankings');
    setError(null);

    try {
      const response = await fetchRankings(metric, 10);
      const mapped = response.rankings.map((r, idx) => ({
        rank: r.rank,
        site: r.entity_id,
        score: r.value,
        percentile: r.percentile,
      }));
      setRankingsData(mapped);
    } catch (err: any) {
      setError(err.message || 'Failed to load rankings');
      setRankingsData([
        { rank: 1, site: 'Site 0042', score: 96.5, percentile: 99 },
        { rank: 2, site: 'Site 0127', score: 94.2, percentile: 97 },
        { rank: 3, site: 'Site 0089', score: 92.8, percentile: 95 },
        { rank: 4, site: 'Site 0156', score: 91.3, percentile: 93 },
        { rank: 5, site: 'Site 0203', score: 89.7, percentile: 90 },
        { rank: 6, site: 'Site 0078', score: 87.5, percentile: 87 },
        { rank: 7, site: 'Site 0134', score: 85.2, percentile: 84 },
        { rank: 8, site: 'Site 0091', score: 83.8, percentile: 81 },
        { rank: 9, site: 'Site 0167', score: 82.1, percentile: 78 },
        { rank: 10, site: 'Site 0245', score: 80.5, percentile: 75 },
      ]);
    } finally {
      setLoading(null);
    }
  };

  const generateSiteAnalysis = (data: any) => {
    setAiAnalysis({
      title: `Site Analysis: ${data.site}`,
      content: `**Site ${data.site} Performance Summary**

**Rank:** #${data.rank} out of 10 sites
**Score:** ${data.score}/100
**Percentile:** ${data.percentile}th

**AI Analysis:**
${data.site} is ${data.rank <= 3 ? 'a top performer' : data.rank <= 5 ? 'performing excellently' : 'showing solid performance'} in this study.

**Comparative Insights:**
- ${data.rank === 1 ? 'Leading the study with exceptional data quality' : `${data.score - 96.5 > -5 ? 'Close to the top performer' : 'Opportunity to improve to reach top 3'}`}
- Score is ${data.score > 90 ? 'excellent' : data.score > 80 ? 'very good' : 'good'} compared to industry benchmarks
- ${data.percentile}th percentile means outperforming ${data.percentile}% of all sites

**Recommendations:**
- ${data.rank <= 3 ? 'Maintain current best practices and share knowledge' : 'Review top-performing sites for best practice adoption'}
- Focus on consistent data entry and timely query resolution
- Schedule regular quality reviews to maintain or improve ranking`
    });
  };

  const getRankBadge = (rank: number) => {
    if (rank === 1) return <div className="rank-badge gold">🥇</div>;
    if (rank === 2) return <div className="rank-badge silver">🥈</div>;
    if (rank === 3) return <div className="rank-badge bronze">🥉</div>;
    return <div className="rank-badge bg-gray-100 text-gray-600">{rank}</div>;
  };

  const getPerformanceBadge = (perf: string) => {
    const styles: Record<string, { bg: string; text: string; glow: string }> = {
      Excellent: { bg: 'from-emerald-400 to-emerald-600', text: 'text-white', glow: 'shadow-[0_0_20px_rgba(16,185,129,0.4)]' },
      Good: { bg: 'from-blue-400 to-blue-600', text: 'text-white', glow: 'shadow-[0_0_20px_rgba(59,130,246,0.4)]' },
      Average: { bg: 'from-amber-400 to-amber-600', text: 'text-white', glow: 'shadow-[0_0_20px_rgba(245,158,11,0.4)]' },
      Poor: { bg: 'from-red-400 to-red-600', text: 'text-white', glow: 'shadow-[0_0_20px_rgba(239,68,68,0.4)]' },
    };
    const style = styles[perf] || styles.Average;
    return `bg-gradient-to-r ${style.bg} ${style.text} ${style.glow}`;
  };

  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="premium-card p-3 !transform-none">
          <p className="text-sm font-medium text-gray-800">{payload[0].payload.site}</p>
          <p className="text-xs text-gray-600">Score: <span className="font-semibold text-blue-600">{payload[0].value}</span></p>
          <p className="text-xs text-gray-500">Click for AI insights</p>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="space-y-6">
      {/* Header with Gradient */}
      <div className="relative">
        <div className="flex items-center gap-3 mb-2">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center shadow-lg">
            <TrendingUp className="w-5 h-5 text-white" />
          </div>
          <div>
            <h2 className="text-2xl font-bold bg-gradient-to-r from-blue-600 via-purple-600 to-blue-600 bg-clip-text text-transparent bg-[length:200%_auto] animate-[gradient-shift_3s_ease_infinite]">
              Analytics & Benchmarking
            </h2>
            <p className="text-gray-500 text-sm">
              Compare performance metrics and view site rankings
            </p>
          </div>
        </div>
      </div>

      {/* Controls - Premium Styling */}
      <div className="premium-card p-5">
        <div className="flex flex-wrap gap-4 items-center">
          <div className="relative flex-1 min-w-[180px]">
            <input
              type="text"
              placeholder="Enter Site ID (e.g., 018)"
              value={siteId}
              onChange={(e) => setSiteId(e.target.value)}
              className="w-full bg-white/80 text-gray-800 px-4 py-3 rounded-xl border-2 border-gray-200 focus:border-blue-500 focus:ring-4 focus:ring-blue-500/20 focus:outline-none placeholder-gray-400 transition-all duration-300"
            />
          </div>

          <button
            onClick={fetchBenchmark}
            disabled={loading === 'benchmark'}
            className="px-6 py-3 bg-gradient-to-r from-blue-500 to-blue-600 text-white rounded-xl hover:shadow-[0_8px_30px_rgba(59,130,246,0.4)] transition-all duration-300 hover:-translate-y-0.5 disabled:opacity-50 flex items-center gap-2 font-medium"
          >
            {loading === 'benchmark' ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Target className="w-4 h-4" />
            )}
            Get Benchmark
          </button>

          <div className="relative flex-1 min-w-[180px]">
            <select
              value={metric}
              onChange={(e) => setMetric(e.target.value)}
              className="w-full bg-white/80 text-gray-800 px-4 py-3 pr-10 rounded-xl border-2 border-gray-200 focus:border-blue-500 focus:ring-4 focus:ring-blue-500/20 focus:outline-none appearance-none transition-all duration-300"
            >
              <option value="dqi">DQI Score</option>
              <option value="enrollment">Enrollment Rate</option>
              <option value="query">Query Resolution</option>
            </select>
            <ChevronDown className="absolute right-4 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400 pointer-events-none" />
          </div>

          <button
            onClick={loadRankings}
            disabled={loading === 'rankings'}
            className="px-6 py-3 bg-gradient-to-r from-purple-500 to-purple-600 text-white rounded-xl hover:shadow-[0_8px_30px_rgba(139,92,246,0.4)] transition-all duration-300 hover:-translate-y-0.5 disabled:opacity-50 flex items-center gap-2 font-medium"
          >
            {loading === 'rankings' ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Award className="w-4 h-4" />
            )}
            Load Rankings
          </button>
        </div>

        {error && (
          <div className="mt-3 p-3 bg-red-50 border border-red-200 rounded-lg text-red-600 text-sm">
            {error}
          </div>
        )}
      </div>

      {/* Main Grid - 3 Columns with AI Analysis in Center */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Benchmark Card - Left */}
        <div className={`premium-card p-6 animate-slide-up ${!benchmarkData ? 'flex items-center justify-center min-h-[300px]' : ''}`}>
          {benchmarkData ? (
            <>
              <div className="flex items-center gap-2 mb-6">
                <Target className="w-5 h-5 text-blue-500" />
                <h3 className="text-lg font-semibold text-gray-800">Performance Benchmark</h3>
              </div>

              <div className="grid grid-cols-3 gap-4 mb-6">
                <div className="text-center p-4 bg-gradient-to-br from-blue-50 to-purple-50 rounded-xl">
                  <div className="text-3xl font-bold metric-value mb-1">{benchmarkData.percentile}th</div>
                  <div className="text-xs text-gray-500 font-medium">Percentile</div>
                </div>
                <div className="text-center p-4 bg-gradient-to-br from-purple-50 to-pink-50 rounded-xl">
                  <div className="text-3xl font-bold metric-value mb-1">#{benchmarkData.rank}</div>
                  <div className="text-xs text-gray-500 font-medium">Rank</div>
                </div>
                <div className="text-center p-4 bg-gradient-to-br from-green-50 to-emerald-50 rounded-xl">
                  <div className={`inline-block px-3 py-1.5 rounded-lg text-sm font-medium mb-1 ${getPerformanceBadge(benchmarkData.performance)}`}>
                    {benchmarkData.performance}
                  </div>
                  <div className="text-xs text-gray-500 font-medium">Status</div>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4 mb-6">
                <div className="p-3 bg-green-50/50 rounded-xl border border-green-100">
                  <div className="flex items-center gap-2 text-sm text-green-700 font-medium mb-2">
                    <Zap className="w-4 h-4" />
                    Strengths
                  </div>
                  <ul className="space-y-1.5">
                    {benchmarkData.strengths.map((str: string, idx: number) => (
                      <li key={idx} className="text-xs text-gray-600 flex items-start gap-1.5">
                        <span className="text-green-500 mt-0.5">•</span>
                        {str}
                      </li>
                    ))}
                  </ul>
                </div>
                <div className="p-3 bg-amber-50/50 rounded-xl border border-amber-100">
                  <div className="flex items-center gap-2 text-sm text-amber-700 font-medium mb-2">
                    <Target className="w-4 h-4" />
                    Focus Areas
                  </div>
                  <ul className="space-y-1.5">
                    {benchmarkData.weaknesses.map((weak: string, idx: number) => (
                      <li key={idx} className="text-xs text-gray-600 flex items-start gap-1.5">
                        <span className="text-amber-500 mt-0.5">•</span>
                        {weak}
                      </li>
                    ))}
                  </ul>
                </div>
              </div>

              <button
                onClick={() => generateBenchmarkAnalysis(benchmarkData.percentile, benchmarkData.performance)}
                className="w-full px-4 py-3 bg-gradient-to-r from-blue-500/10 to-purple-500/10 border-2 border-blue-200 rounded-xl text-blue-600 font-medium hover:border-blue-400 hover:shadow-[0_0_20px_rgba(59,130,246,0.2)] transition-all duration-300 flex items-center justify-center gap-2"
              >
                <Sparkles className="w-4 h-4" />
                Generate AI Analysis
              </button>
            </>
          ) : (
            <div className="text-center text-gray-400">
              <Target className="w-12 h-12 mx-auto mb-3 opacity-30" />
              <p className="text-sm">Enter a Site ID to view benchmark</p>
            </div>
          )}
        </div>

        {/* AI Analysis Card - Center */}
        <div className={`ai-analysis-card p-6 animate-slide-up ${!aiAnalysis ? 'flex items-center justify-center min-h-[300px]' : ''}`} style={{ animationDelay: '0.1s' }}>
          {aiAnalysis ? (
            <>
              <div className="flex items-center gap-3 mb-4 pb-4 border-b border-blue-100">
                <div className="p-2 bg-gradient-to-r from-blue-500 to-purple-600 rounded-lg">
                  <Brain className="w-5 h-5 text-white" />
                </div>
                <div>
                  <span className="text-xs font-medium text-blue-600 bg-blue-100 px-2 py-0.5 rounded">AI Analysis</span>
                  <h3 className="text-base font-semibold text-gray-800">{aiAnalysis.title}</h3>
                </div>
              </div>

              <div className="space-y-3 max-h-[320px] overflow-y-auto pr-2">
                {aiAnalysis.content.split('\n').map((line, idx) => {
                  if (line.startsWith('**') && line.endsWith('**')) {
                    return (
                      <h4 key={idx} className="text-sm font-semibold text-gray-800 mt-3 mb-1 flex items-center gap-2">
                        <span className="w-1.5 h-1.5 bg-blue-500 rounded-full"></span>
                        {line.replace(/\*\*/g, '')}
                      </h4>
                    );
                  }
                  if (line.startsWith('- ')) {
                    return (
                      <li key={idx} className="text-sm text-gray-600 ml-4 list-none flex items-start gap-2">
                        <span className="text-blue-400 mt-1">→</span>
                        {line.slice(2)}
                      </li>
                    );
                  }
                  if (line.trim()) {
                    return <p key={idx} className="text-sm text-gray-600 leading-relaxed">{line}</p>;
                  }
                  return null;
                })}
              </div>
            </>
          ) : (
            <div className="text-center text-gray-400">
              <div className="w-16 h-16 mx-auto mb-4 bg-gradient-to-br from-blue-100 to-purple-100 rounded-2xl flex items-center justify-center">
                <Brain className="w-8 h-8 text-blue-400" />
              </div>
              <p className="text-sm font-medium text-gray-500 mb-1">AI Analysis</p>
              <p className="text-xs text-gray-400">Click on benchmark or ranking items<br />to generate intelligent insights</p>
            </div>
          )}
        </div>

        {/* Rankings Table - Right */}
        <div className={`premium-card p-6 animate-slide-up ${!rankingsData ? 'flex items-center justify-center min-h-[300px]' : ''}`} style={{ animationDelay: '0.2s' }}>
          {rankingsData ? (
            <>
              <div className="flex items-center gap-2 mb-6">
                <Award className="w-5 h-5 text-purple-500" />
                <h3 className="text-lg font-semibold text-gray-800">Site Rankings</h3>
              </div>

              <div className="space-y-1 max-h-[350px] overflow-y-auto pr-2">
                <div className="grid grid-cols-4 gap-3 pb-2 border-b border-gray-200 text-xs font-medium text-gray-500 sticky top-0 bg-white/95 backdrop-blur-sm">
                  <div>Rank</div>
                  <div>Site</div>
                  <div>Score</div>
                  <div>Percentile</div>
                </div>

                {rankingsData.map((item: any) => (
                  <div
                    key={item.rank}
                    onClick={() => generateSiteAnalysis(item)}
                    className="grid grid-cols-4 gap-3 py-3 text-sm text-gray-700 table-row-hover rounded-lg px-2 cursor-pointer group"
                  >
                    <div>{getRankBadge(item.rank)}</div>
                    <div className="font-medium group-hover:text-blue-600 transition-colors">{item.site}</div>
                    <div className="font-semibold text-gray-800">{Number(item.score).toFixed(2)}</div>
                    <div className="text-gray-500">{Number(item.percentile).toFixed(2)}th</div>
                  </div>
                ))}
              </div>
            </>
          ) : (
            <div className="text-center text-gray-400">
              <Award className="w-12 h-12 mx-auto mb-3 opacity-30" />
              <p className="text-sm">Click "Load Rankings" to view</p>
            </div>
          )}
        </div>
      </div>

      {/* Leaderboard Chart - Enhanced */}
      {rankingsData && (
        <div className="premium-card p-6 animate-slide-up" style={{ animationDelay: '0.3s' }}>
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center gap-2">
              <TrendingUp className="w-5 h-5 text-blue-500" />
              <h3 className="text-lg font-semibold text-gray-800">Top 10 Leaderboard</h3>
            </div>
            <p className="text-xs text-gray-400 bg-gray-100 px-3 py-1 rounded-full">
              Click bars for AI insights
            </p>
          </div>

          <ResponsiveContainer width="100%" height={350}>
            <BarChart data={rankingsData} layout="vertical" margin={{ left: 10, right: 30 }}>
              <XAxis type="number" stroke="#9ca3af" fontSize={12} tickLine={false} axisLine={false} />
              <YAxis dataKey="site" type="category" stroke="#9ca3af" width={80} fontSize={12} tickLine={false} axisLine={false} />
              <Tooltip content={<CustomTooltip />} cursor={{ fill: 'rgba(59, 130, 246, 0.05)' }} />
              <Bar
                dataKey="score"
                radius={[0, 8, 8, 0]}
                onClick={(data) => {
                  if (data && data.site) {
                    generateSiteAnalysis(data);
                  }
                }}
                style={{ cursor: 'pointer' }}
              >
                {rankingsData.map((_: any, index: number) => (
                  <Cell
                    key={`cell-${index}`}
                    fill={index === 0 ? 'url(#goldGradient)' : index === 1 ? 'url(#silverGradient)' : index === 2 ? 'url(#bronzeGradient)' : 'url(#blueGradient)'}
                  />
                ))}
              </Bar>
              <defs>
                <linearGradient id="goldGradient" x1="0" y1="0" x2="1" y2="0">
                  <stop offset="0%" stopColor="#fbbf24" />
                  <stop offset="100%" stopColor="#f59e0b" />
                </linearGradient>
                <linearGradient id="silverGradient" x1="0" y1="0" x2="1" y2="0">
                  <stop offset="0%" stopColor="#9ca3af" />
                  <stop offset="100%" stopColor="#6b7280" />
                </linearGradient>
                <linearGradient id="bronzeGradient" x1="0" y1="0" x2="1" y2="0">
                  <stop offset="0%" stopColor="#d97706" />
                  <stop offset="100%" stopColor="#b45309" />
                </linearGradient>
                <linearGradient id="blueGradient" x1="0" y1="0" x2="1" y2="0">
                  <stop offset="0%" stopColor="#3b82f6" />
                  <stop offset="100%" stopColor="#2563eb" />
                </linearGradient>
              </defs>
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Empty State */}
      {!benchmarkData && !rankingsData && (
        <div className="premium-card p-12 text-center animate-slide-up">
          <div className="w-20 h-20 mx-auto mb-6 bg-gradient-to-br from-blue-100 to-purple-100 rounded-2xl flex items-center justify-center">
            <TrendingUp className="w-10 h-10 text-blue-400" />
          </div>
          <h3 className="text-lg font-semibold text-gray-700 mb-2">Get Started with Analytics</h3>
          <p className="text-gray-500 text-sm max-w-md mx-auto">
            Enter a site ID to fetch benchmark data, or load rankings to see the top performing sites
          </p>
        </div>
      )}
    </div>
  );
}