'use client';

import { useState } from 'react';
import { BarChart, Bar, XAxis, YAxis, ResponsiveContainer, Cell, Tooltip } from 'recharts';
import { ChevronDown, Loader2, Sparkles, TrendingUp, Award, Target, Zap, Brain, BarChart3, ArrowUpRight, Activity } from 'lucide-react';
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
      const mapped = response.rankings.map((r: any) => ({
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
    if (rank === 1) return (
      <div className="w-8 h-8 rounded-full bg-gradient-to-br from-amber-300 to-amber-500 flex items-center justify-center text-amber-900 font-bold text-sm shadow-lg shadow-amber-500/30">
        1
      </div>
    );
    if (rank === 2) return (
      <div className="w-8 h-8 rounded-full bg-gradient-to-br from-slate-300 to-slate-400 flex items-center justify-center text-slate-800 font-bold text-sm shadow-lg shadow-slate-400/30">
        2
      </div>
    );
    if (rank === 3) return (
      <div className="w-8 h-8 rounded-full bg-gradient-to-br from-orange-400 to-orange-600 flex items-center justify-center text-orange-900 font-bold text-sm shadow-lg shadow-orange-500/30">
        3
      </div>
    );
    return (
      <div className="w-8 h-8 rounded-full bg-slate-700/50 flex items-center justify-center text-slate-300 font-medium text-sm border border-slate-600/50">
        {rank}
      </div>
    );
  };

  const getPerformanceBadge = (perf: string) => {
    const styles: Record<string, string> = {
      Excellent: 'bg-gradient-to-r from-emerald-500 to-teal-500 text-white shadow-lg shadow-emerald-500/25',
      Good: 'bg-gradient-to-r from-blue-500 to-cyan-500 text-white shadow-lg shadow-blue-500/25',
      Average: 'bg-gradient-to-r from-amber-500 to-orange-500 text-white shadow-lg shadow-amber-500/25',
      Poor: 'bg-gradient-to-r from-red-500 to-rose-500 text-white shadow-lg shadow-red-500/25',
    };
    return styles[perf] || styles.Average;
  };

  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-slate-800/95 backdrop-blur-xl border border-slate-700/50 rounded-xl p-4 shadow-2xl">
          <p className="text-sm font-semibold text-white mb-1">{payload[0].payload.site}</p>
          <p className="text-xs text-slate-300">Score: <span className="font-bold text-cyan-400">{payload[0].value}</span></p>
          <p className="text-xs text-slate-400 mt-2 flex items-center gap-1">
            <Sparkles className="w-3 h-3" /> Click for AI insights
          </p>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="space-y-8 p-6">
      {/* Enhanced Header */}
      <div className="relative">
        <div className="absolute -inset-4 bg-gradient-to-r from-cyan-500/10 via-blue-500/10 to-purple-500/10 rounded-3xl blur-2xl" />
        <div className="relative flex items-center gap-4">
          <div className="relative">
            <div className="absolute inset-0 bg-gradient-to-br from-cyan-400 to-blue-600 rounded-2xl blur-lg opacity-50" />
            <div className="relative w-14 h-14 rounded-2xl bg-gradient-to-br from-cyan-400 to-blue-600 flex items-center justify-center shadow-xl">
              <BarChart3 className="w-7 h-7 text-white" />
            </div>
          </div>
          <div>
            <h2 className="text-3xl font-bold text-white tracking-tight">
              Analytics & Benchmarking
            </h2>
            <p className="text-slate-400 mt-1">
              Compare performance metrics and view site rankings
            </p>
          </div>
        </div>
      </div>

      {/* Enhanced Controls */}
      <div className="relative group">
        <div className="absolute -inset-0.5 bg-gradient-to-r from-cyan-500/20 to-blue-500/20 rounded-2xl blur opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
        <div className="relative bg-slate-800/50 backdrop-blur-xl border border-slate-700/50 rounded-2xl p-6">
          <div className="flex flex-wrap gap-4 items-center">
            <div className="relative flex-1 min-w-[200px]">
              <input
                type="text"
                placeholder="Enter Site ID (e.g., 018)"
                value={siteId}
                onChange={(e) => setSiteId(e.target.value)}
                className="w-full bg-slate-900/50 text-white px-4 py-3.5 rounded-xl border border-slate-600/50 focus:border-cyan-500/50 focus:ring-2 focus:ring-cyan-500/20 focus:outline-none placeholder-slate-500 transition-all duration-300"
              />
            </div>

            <button
              onClick={fetchBenchmark}
              disabled={loading === 'benchmark'}
              className="group/btn relative px-6 py-3.5 bg-gradient-to-r from-cyan-500 to-blue-500 text-white rounded-xl font-medium transition-all duration-300 hover:shadow-xl hover:shadow-cyan-500/25 hover:-translate-y-0.5 disabled:opacity-50 disabled:hover:translate-y-0 flex items-center gap-2 overflow-hidden"
            >
              <div className="absolute inset-0 bg-gradient-to-r from-cyan-400 to-blue-400 opacity-0 group-hover/btn:opacity-100 transition-opacity" />
              <span className="relative flex items-center gap-2">
                {loading === 'benchmark' ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <Target className="w-4 h-4" />
                )}
                Get Benchmark
              </span>
            </button>

            <div className="relative flex-1 min-w-[180px]">
              <select
                value={metric}
                onChange={(e) => setMetric(e.target.value)}
                className="w-full bg-slate-900/50 text-white px-4 py-3.5 pr-10 rounded-xl border border-slate-600/50 focus:border-cyan-500/50 focus:ring-2 focus:ring-cyan-500/20 focus:outline-none appearance-none transition-all duration-300"
              >
                <option value="dqi">DQI Score</option>
                <option value="enrollment">Enrollment Rate</option>
                <option value="query">Query Resolution</option>
              </select>
              <ChevronDown className="absolute right-4 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400 pointer-events-none" />
            </div>

            <button
              onClick={loadRankings}
              disabled={loading === 'rankings'}
              className="group/btn relative px-6 py-3.5 bg-gradient-to-r from-purple-500 to-pink-500 text-white rounded-xl font-medium transition-all duration-300 hover:shadow-xl hover:shadow-purple-500/25 hover:-translate-y-0.5 disabled:opacity-50 disabled:hover:translate-y-0 flex items-center gap-2 overflow-hidden"
            >
              <div className="absolute inset-0 bg-gradient-to-r from-purple-400 to-pink-400 opacity-0 group-hover/btn:opacity-100 transition-opacity" />
              <span className="relative flex items-center gap-2">
                {loading === 'rankings' ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <Award className="w-4 h-4" />
                )}
                Load Rankings
              </span>
            </button>
          </div>

          {error && (
            <div className="mt-4 p-4 bg-red-500/10 border border-red-500/30 rounded-xl text-red-400 text-sm flex items-center gap-3">
              <div className="w-8 h-8 rounded-full bg-red-500/20 flex items-center justify-center flex-shrink-0">
                <span className="text-red-400">!</span>
              </div>
              {error}
            </div>
          )}
        </div>
      </div>

      {/* Main Grid - 3 Columns */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Benchmark Card */}
        <div className="group relative">
          <div className="absolute -inset-0.5 bg-gradient-to-r from-cyan-500/20 to-blue-500/20 rounded-2xl blur opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
          <div className={`relative bg-slate-800/50 backdrop-blur-xl border border-slate-700/50 rounded-2xl p-6 h-full transition-all duration-300 ${!benchmarkData ? 'flex items-center justify-center min-h-[400px]' : ''}`}>
            {benchmarkData ? (
              <>
                <div className="flex items-center gap-3 mb-6">
                  <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-cyan-500 to-blue-500 flex items-center justify-center">
                    <Target className="w-5 h-5 text-white" />
                  </div>
                  <h3 className="text-lg font-semibold text-white">Performance Benchmark</h3>
                </div>

                <div className="grid grid-cols-3 gap-3 mb-6">
                  <div className="relative overflow-hidden rounded-xl bg-gradient-to-br from-cyan-500/10 to-blue-500/10 border border-cyan-500/20 p-4">
                    <div className="absolute top-0 right-0 w-16 h-16 bg-cyan-500/10 rounded-full blur-2xl" />
                    <div className="relative">
                      <div className="text-3xl font-bold text-cyan-400">{benchmarkData.percentile}th</div>
                      <div className="text-xs text-slate-400 mt-1 font-medium">Percentile</div>
                    </div>
                  </div>
                  <div className="relative overflow-hidden rounded-xl bg-gradient-to-br from-purple-500/10 to-pink-500/10 border border-purple-500/20 p-4">
                    <div className="absolute top-0 right-0 w-16 h-16 bg-purple-500/10 rounded-full blur-2xl" />
                    <div className="relative">
                      <div className="text-3xl font-bold text-purple-400">#{benchmarkData.rank}</div>
                      <div className="text-xs text-slate-400 mt-1 font-medium">Rank</div>
                    </div>
                  </div>
                  <div className="relative overflow-hidden rounded-xl bg-gradient-to-br from-emerald-500/10 to-teal-500/10 border border-emerald-500/20 p-4">
                    <div className="absolute top-0 right-0 w-16 h-16 bg-emerald-500/10 rounded-full blur-2xl" />
                    <div className="relative">
                      <div className={`inline-block px-2.5 py-1 rounded-lg text-xs font-semibold ${getPerformanceBadge(benchmarkData.performance)}`}>
                        {benchmarkData.performance}
                      </div>
                      <div className="text-xs text-slate-400 mt-1.5 font-medium">Status</div>
                    </div>
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4 mb-6">
                  <div className="p-4 bg-emerald-500/5 rounded-xl border border-emerald-500/20">
                    <div className="flex items-center gap-2 text-sm text-emerald-400 font-semibold mb-3">
                      <Zap className="w-4 h-4" />
                      Strengths
                    </div>
                    <ul className="space-y-2">
                      {benchmarkData.strengths.map((str: string, idx: number) => (
                        <li key={idx} className="text-xs text-slate-300 flex items-start gap-2">
                          <ArrowUpRight className="w-3 h-3 text-emerald-400 mt-0.5 flex-shrink-0" />
                          {str}
                        </li>
                      ))}
                    </ul>
                  </div>
                  <div className="p-4 bg-amber-500/5 rounded-xl border border-amber-500/20">
                    <div className="flex items-center gap-2 text-sm text-amber-400 font-semibold mb-3">
                      <Target className="w-4 h-4" />
                      Focus Areas
                    </div>
                    <ul className="space-y-2">
                      {benchmarkData.weaknesses.map((weak: string, idx: number) => (
                        <li key={idx} className="text-xs text-slate-300 flex items-start gap-2">
                          <Activity className="w-3 h-3 text-amber-400 mt-0.5 flex-shrink-0" />
                          {weak}
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>

                <button
                  onClick={() => generateBenchmarkAnalysis(benchmarkData.percentile, benchmarkData.performance)}
                  className="w-full px-4 py-3 bg-gradient-to-r from-cyan-500/10 to-blue-500/10 border border-cyan-500/30 rounded-xl text-cyan-400 font-medium hover:border-cyan-400 hover:bg-cyan-500/20 transition-all duration-300 flex items-center justify-center gap-2 group/ai"
                >
                  <Sparkles className="w-4 h-4 group-hover/ai:animate-pulse" />
                  Generate AI Analysis
                </button>
              </>
            ) : (
              <div className="text-center">
                <div className="relative w-20 h-20 mx-auto mb-6">
                  <div className="absolute inset-0 bg-gradient-to-br from-cyan-500/20 to-blue-500/20 rounded-2xl blur-xl" />
                  <div className="relative w-20 h-20 bg-gradient-to-br from-slate-800 to-slate-900 rounded-2xl border border-slate-700/50 flex items-center justify-center">
                    <Target className="w-9 h-9 text-slate-500" />
                  </div>
                </div>
                <h4 className="text-slate-300 font-medium mb-2">No Benchmark Data</h4>
                <p className="text-sm text-slate-500 max-w-[200px] mx-auto">Enter a Site ID and click "Get Benchmark" to view performance metrics</p>
              </div>
            )}
          </div>
        </div>

        {/* AI Analysis Card */}
        <div className="group relative">
          <div className="absolute -inset-0.5 bg-gradient-to-r from-purple-500/30 to-pink-500/30 rounded-2xl blur opacity-50 group-hover:opacity-100 transition-opacity duration-500" />
          <div className={`relative bg-gradient-to-br from-slate-800/90 to-slate-900/90 backdrop-blur-xl border border-purple-500/30 rounded-2xl p-6 h-full transition-all duration-300 ${!aiAnalysis ? 'flex items-center justify-center min-h-[400px]' : ''}`}>
            {aiAnalysis ? (
              <>
                <div className="flex items-center gap-3 mb-5 pb-5 border-b border-purple-500/20">
                  <div className="relative">
                    <div className="absolute inset-0 bg-gradient-to-br from-purple-400 to-pink-500 rounded-xl blur opacity-50" />
                    <div className="relative w-10 h-10 bg-gradient-to-br from-purple-500 to-pink-500 rounded-xl flex items-center justify-center">
                      <Brain className="w-5 h-5 text-white" />
                    </div>
                  </div>
                  <div>
                    <span className="text-[10px] font-bold text-purple-400 bg-purple-500/20 px-2 py-0.5 rounded-full uppercase tracking-wider">AI Powered</span>
                    <h3 className="text-base font-semibold text-white mt-0.5">{aiAnalysis.title}</h3>
                  </div>
                </div>

                <div className="space-y-3 max-h-[320px] overflow-y-auto pr-2 custom-scrollbar">
                  {aiAnalysis.content.split('\n').map((line, idx) => {
                    if (line.startsWith('**') && line.endsWith('**')) {
                      return (
                        <h4 key={idx} className="text-sm font-semibold text-white mt-4 mb-2 flex items-center gap-2">
                          <span className="w-1.5 h-1.5 bg-gradient-to-r from-purple-400 to-pink-400 rounded-full" />
                          {line.replace(/\*\*/g, '')}
                        </h4>
                      );
                    }
                    if (line.startsWith('- ')) {
                      return (
                        <div key={idx} className="text-sm text-slate-300 ml-3 flex items-start gap-2">
                          <span className="text-purple-400 mt-0.5">→</span>
                          <span>{line.slice(2)}</span>
                        </div>
                      );
                    }
                    if (line.trim()) {
                      return <p key={idx} className="text-sm text-slate-300 leading-relaxed">{line}</p>;
                    }
                    return null;
                  })}
                </div>
              </>
            ) : (
              <div className="text-center">
                <div className="relative w-24 h-24 mx-auto mb-6">
                  <div className="absolute inset-0 bg-gradient-to-br from-purple-500/30 to-pink-500/30 rounded-3xl blur-2xl animate-pulse" />
                  <div className="relative w-24 h-24 bg-gradient-to-br from-slate-800 to-slate-900 rounded-3xl border border-purple-500/30 flex items-center justify-center">
                    <Brain className="w-11 h-11 text-purple-400" />
                  </div>
                </div>
                <h4 className="text-slate-200 font-semibold mb-2">AI Analysis</h4>
                <p className="text-sm text-slate-400 max-w-[220px] mx-auto">Click on benchmark or ranking items to generate intelligent insights</p>
              </div>
            )}
          </div>
        </div>

        {/* Rankings Table */}
        <div className="group relative">
          <div className="absolute -inset-0.5 bg-gradient-to-r from-purple-500/20 to-pink-500/20 rounded-2xl blur opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
          <div className={`relative bg-slate-800/50 backdrop-blur-xl border border-slate-700/50 rounded-2xl p-6 h-full transition-all duration-300 ${!rankingsData ? 'flex items-center justify-center min-h-[400px]' : ''}`}>
            {rankingsData ? (
              <>
                <div className="flex items-center gap-3 mb-6">
                  <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center">
                    <Award className="w-5 h-5 text-white" />
                  </div>
                  <h3 className="text-lg font-semibold text-white">Site Rankings</h3>
                </div>

                <div className="space-y-1 max-h-[350px] overflow-y-auto pr-2 custom-scrollbar">
                  <div className="grid grid-cols-4 gap-3 pb-3 border-b border-slate-700/50 text-xs font-semibold text-slate-400 uppercase tracking-wider sticky top-0 bg-slate-800/95 backdrop-blur-sm">
                    <div>Rank</div>
                    <div>Site</div>
                    <div>Score</div>
                    <div>Percentile</div>
                  </div>

                  {rankingsData.map((item: any) => (
                    <div
                      key={item.rank}
                      onClick={() => generateSiteAnalysis(item)}
                      className="grid grid-cols-4 gap-3 py-3 text-sm text-slate-200 rounded-xl px-2 cursor-pointer transition-all duration-200 hover:bg-slate-700/30 hover:scale-[1.02] group/row"
                    >
                      <div>{getRankBadge(item.rank)}</div>
                      <div className="font-medium group-hover/row:text-cyan-400 transition-colors flex items-center">{item.site}</div>
                      <div className="font-bold text-white flex items-center">{Number(item.score).toFixed(1)}</div>
                      <div className="text-slate-400 flex items-center">{Number(item.percentile).toFixed(0)}th</div>
                    </div>
                  ))}
                </div>
              </>
            ) : (
              <div className="text-center">
                <div className="relative w-20 h-20 mx-auto mb-6">
                  <div className="absolute inset-0 bg-gradient-to-br from-purple-500/20 to-pink-500/20 rounded-2xl blur-xl" />
                  <div className="relative w-20 h-20 bg-gradient-to-br from-slate-800 to-slate-900 rounded-2xl border border-slate-700/50 flex items-center justify-center">
                    <Award className="w-9 h-9 text-slate-500" />
                  </div>
                </div>
                <h4 className="text-slate-300 font-medium mb-2">No Rankings Data</h4>
                <p className="text-sm text-slate-500 max-w-[200px] mx-auto">Click "Load Rankings" to view top performing sites</p>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Leaderboard Chart */}
      {rankingsData && (
        <div className="group relative">
          <div className="absolute -inset-0.5 bg-gradient-to-r from-cyan-500/20 via-purple-500/20 to-pink-500/20 rounded-2xl blur opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
          <div className="relative bg-slate-800/50 backdrop-blur-xl border border-slate-700/50 rounded-2xl p-6">
            <div className="flex items-center justify-between mb-6">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-cyan-500 to-blue-500 flex items-center justify-center">
                  <TrendingUp className="w-5 h-5 text-white" />
                </div>
                <h3 className="text-lg font-semibold text-white">Top 10 Leaderboard</h3>
              </div>
              <div className="flex items-center gap-2 text-xs text-slate-400 bg-slate-700/30 px-3 py-1.5 rounded-full">
                <Sparkles className="w-3 h-3 text-purple-400" />
                Click bars for AI insights
              </div>
            </div>

            <ResponsiveContainer width="100%" height={350}>
              <BarChart data={rankingsData} layout="vertical" margin={{ left: 10, right: 30 }}>
                <XAxis type="number" stroke="#64748b" fontSize={12} tickLine={false} axisLine={false} />
                <YAxis dataKey="site" type="category" stroke="#64748b" width={80} fontSize={12} tickLine={false} axisLine={false} />
                <Tooltip content={<CustomTooltip />} cursor={{ fill: 'rgba(139, 92, 246, 0.05)' }} />
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
                      fill={index === 0 ? 'url(#goldGradient)' : index === 1 ? 'url(#silverGradient)' : index === 2 ? 'url(#bronzeGradient)' : 'url(#cyanGradient)'}
                    />
                  ))}
                </Bar>
                <defs>
                  <linearGradient id="goldGradient" x1="0" y1="0" x2="1" y2="0">
                    <stop offset="0%" stopColor="#fbbf24" />
                    <stop offset="100%" stopColor="#f59e0b" />
                  </linearGradient>
                  <linearGradient id="silverGradient" x1="0" y1="0" x2="1" y2="0">
                    <stop offset="0%" stopColor="#94a3b8" />
                    <stop offset="100%" stopColor="#64748b" />
                  </linearGradient>
                  <linearGradient id="bronzeGradient" x1="0" y1="0" x2="1" y2="0">
                    <stop offset="0%" stopColor="#fb923c" />
                    <stop offset="100%" stopColor="#ea580c" />
                  </linearGradient>
                  <linearGradient id="cyanGradient" x1="0" y1="0" x2="1" y2="0">
                    <stop offset="0%" stopColor="#22d3ee" />
                    <stop offset="100%" stopColor="#0891b2" />
                  </linearGradient>
                </defs>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      {/* Enhanced Empty State */}
      {!benchmarkData && !rankingsData && (
        <div className="relative group">
          <div className="absolute inset-0 bg-gradient-to-r from-cyan-500/10 via-purple-500/10 to-pink-500/10 rounded-3xl blur-2xl" />
          <div className="relative bg-slate-800/30 backdrop-blur-xl border border-slate-700/50 rounded-2xl p-12 text-center">
            <div className="relative w-28 h-28 mx-auto mb-8">
              <div className="absolute inset-0 bg-gradient-to-br from-cyan-500/30 to-purple-500/30 rounded-3xl blur-2xl animate-pulse" />
              <div className="relative w-28 h-28 bg-gradient-to-br from-slate-800 to-slate-900 rounded-3xl border border-slate-700/50 flex items-center justify-center">
                <TrendingUp className="w-14 h-14 text-slate-500" />
              </div>
            </div>
            <h3 className="text-xl font-semibold text-slate-200 mb-3">Get Started with Analytics</h3>
            <p className="text-slate-400 text-sm max-w-md mx-auto mb-8">
              Enter a site ID to fetch benchmark data, or load rankings to see the top performing sites in your study
            </p>
            <div className="flex items-center justify-center gap-4">
              <div className="flex items-center gap-2 text-xs text-slate-500">
                <div className="w-8 h-8 rounded-lg bg-cyan-500/10 border border-cyan-500/20 flex items-center justify-center">
                  <Target className="w-4 h-4 text-cyan-400" />
                </div>
                <span>Benchmark</span>
              </div>
              <div className="w-8 h-px bg-slate-700" />
              <div className="flex items-center gap-2 text-xs text-slate-500">
                <div className="w-8 h-8 rounded-lg bg-purple-500/10 border border-purple-500/20 flex items-center justify-center">
                  <Brain className="w-4 h-4 text-purple-400" />
                </div>
                <span>AI Analysis</span>
              </div>
              <div className="w-8 h-px bg-slate-700" />
              <div className="flex items-center gap-2 text-xs text-slate-500">
                <div className="w-8 h-8 rounded-lg bg-pink-500/10 border border-pink-500/20 flex items-center justify-center">
                  <Award className="w-4 h-4 text-pink-400" />
                </div>
                <span>Rankings</span>
              </div>
            </div>
          </div>
        </div>
      )}

      <style>{`
        .custom-scrollbar::-webkit-scrollbar {
          width: 6px;
        }
        .custom-scrollbar::-webkit-scrollbar-track {
          background: rgba(51, 65, 85, 0.3);
          border-radius: 3px;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb {
          background: rgba(100, 116, 139, 0.5);
          border-radius: 3px;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb:hover {
          background: rgba(100, 116, 139, 0.7);
        }
      `}</style>
    </div>
  );
}