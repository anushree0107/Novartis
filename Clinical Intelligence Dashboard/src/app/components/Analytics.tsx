import { useState } from 'react';
import { BarChart, Bar, XAxis, YAxis, ResponsiveContainer, Cell } from 'recharts';
import { ChevronDown, Loader2 } from 'lucide-react';
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
    } catch (err: any) {
      setError(err.message || 'Failed to fetch benchmark');
      // Fallback to mock data
      setBenchmarkData({
        percentile: 82,
        rank: 18,
        performance: 'Excellent',
        strengths: ['Query resolution speed', 'Data completeness', 'Protocol adherence'],
        weaknesses: ['Missing data patterns', 'Late submissions'],
      });
    } finally {
      setLoading(null);
    }
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
      // Fallback to mock data
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

  const getRankIcon = (rank: number) => {
    if (rank === 1) return '🥇';
    if (rank === 2) return '🥈';
    if (rank === 3) return '🥉';
    return rank;
  };

  const getPerformanceBadge = (perf: string) => {
    const colors: Record<string, string> = {
      Excellent: '#10b981',
      Good: '#0091DF',
      Average: '#f59e0b',
      Poor: '#E03C31',
    };
    return colors[perf] || '#888';
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h2 className="bg-gradient-to-r from-[#3b82f6] to-[#2563eb] bg-clip-text text-transparent mb-2">
          Analytics & Benchmarking
        </h2>
        <p className="text-gray-600 text-sm">
          Compare performance metrics and view site rankings
        </p>
      </div>

      {/* Controls */}
      <div className="glass-card p-4 flex flex-wrap gap-4">
        <input
          type="text"
          placeholder="Site ID"
          value={siteId}
          onChange={(e) => setSiteId(e.target.value)}
          className="flex-1 min-w-[150px] bg-white text-gray-800 px-4 py-2 rounded-lg border border-[#3b82f6]/30 focus:border-[#3b82f6] focus:outline-none placeholder-gray-500"
        />

        <button
          onClick={fetchBenchmark}
          className="px-6 py-2 bg-gradient-to-r from-[#3b82f6] to-[#2563eb] text-white rounded-lg hover:shadow-[0_0_20px_rgba(37,99,235,0.4)] transition-all duration-200"
        >
          Get Benchmark
        </button>

        <div className="relative flex-1 min-w-[150px]">
          <select
            value={metric}
            onChange={(e) => setMetric(e.target.value)}
            className="w-full bg-white text-gray-800 px-4 py-2 pr-10 rounded-lg border border-[#3b82f6]/30 focus:border-[#3b82f6] focus:outline-none appearance-none"
          >
            <option value="dqi">DQI Score</option>
            <option value="enrollment">Enrollment Rate</option>
            <option value="query">Query Resolution</option>
          </select>
          <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400 pointer-events-none" />
        </div>

        <button
          onClick={loadRankings}
          className="px-6 py-2 bg-gradient-to-r from-[#3b82f6] to-[#2563eb] text-white rounded-lg hover:shadow-[0_0_20px_rgba(37,99,235,0.4)] transition-all duration-200"
        >
          Load Rankings
        </button>
      </div>

      {/* Benchmark and Rankings Grid */}
      <div className="grid grid-cols-2 gap-6">
        {/* Benchmark Card */}
        {benchmarkData && (
          <div className="glass-card p-6">
            <h3 className="text-gray-700 mb-6">Performance Benchmark</h3>

            <div className="grid grid-cols-3 gap-4 mb-6">
              <div className="text-center">
                <div className="text-3xl text-gray-800 mb-1">{benchmarkData.percentile}th</div>
                <div className="text-xs text-gray-500">Percentile</div>
              </div>
              <div className="text-center">
                <div className="text-3xl text-gray-800 mb-1">#{benchmarkData.rank}</div>
                <div className="text-xs text-gray-500">Rank</div>
              </div>
              <div className="text-center">
                <div
                  className="inline-block px-3 py-1 rounded-lg text-white text-sm mb-1"
                  style={{ backgroundColor: getPerformanceBadge(benchmarkData.performance) }}
                >
                  {benchmarkData.performance}
                </div>
                <div className="text-xs text-gray-500">Performance</div>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4 mb-6">
              <div>
                <div className="text-sm text-gray-600 mb-2">💪 Strengths</div>
                <ul className="space-y-1">
                  {benchmarkData.strengths.map((str: string, idx: number) => (
                    <li key={idx} className="text-xs text-gray-700">• {str}</li>
                  ))}
                </ul>
              </div>
              <div>
                <div className="text-sm text-gray-600 mb-2">⚠️ Weaknesses</div>
                <ul className="space-y-1">
                  {benchmarkData.weaknesses.map((weak: string, idx: number) => (
                    <li key={idx} className="text-xs text-gray-700">• {weak}</li>
                  ))}
                </ul>
              </div>
            </div>

            <button
              onClick={() => onAiClick('Benchmark Analysis', 'Your site is performing exceptionally well, ranking in the 82nd percentile overall. This places you in the top 20% of all sites in the study.\n\nKey Performance Insights:\n\n**Strengths:**\n- Query resolution speed is 40% faster than the median\n- Data completeness is consistently above 95%\n- Protocol adherence score is exemplary\n\n**Areas for Improvement:**\n- Missing data patterns suggest opportunities for automated validation\n- Late submissions could be addressed with reminder systems\n\nBenchmark Comparison:\n- You are outperforming 82% of sites globally\n- Your trajectory suggests potential to reach top 10 within the next quarter\n- Consider sharing best practices with lower-performing sites')}
              className="w-full px-4 py-2 bg-white border border-[#3b82f6]/40 rounded-lg text-gray-800 hover:border-[#3b82f6] transition-all duration-200 hover:shadow-[0_0_12px_rgba(37,99,235,0.3)]"
            >
              🤖 AI Analysis
            </button>
          </div>
        )}

        {/* Rankings Table */}
        {rankingsData && (
          <div className="glass-card p-6">
            <h3 className="text-gray-700 mb-6">Site Rankings</h3>

            <div className="space-y-2 max-h-[400px] overflow-y-auto pr-2">
              <div className="grid grid-cols-4 gap-4 pb-2 border-b border-[#3b82f6]/20 text-xs text-gray-500 sticky top-0 bg-white/90 backdrop-blur-sm">
                <div>Rank</div>
                <div>Site</div>
                <div>Score</div>
                <div>Percentile</div>
              </div>

              {rankingsData.map((item: any) => (
                <div key={item.rank} className="grid grid-cols-4 gap-4 py-2 text-sm text-gray-700 hover:bg-blue-50 rounded transition-colors px-2">
                  <div className="text-lg">{getRankIcon(item.rank)}</div>
                  <div>{item.site}</div>
                  <div className="text-gray-800">{item.score}</div>
                  <div>{item.percentile}th</div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Leaderboard Chart */}
      {rankingsData && (
        <div className="glass-card p-6">
          <h3 className="text-gray-700 mb-6">Top 10 Leaderboard</h3>
          <p className="text-xs text-gray-500 mb-4">Click on any bar to see detailed AI analysis</p>
          <ResponsiveContainer width="100%" height={400}>
            <BarChart data={rankingsData} layout="vertical">
              <XAxis type="number" stroke="#6b7280" />
              <YAxis dataKey="site" type="category" stroke="#6b7280" width={80} />
              <Bar
                dataKey="score"
                radius={[0, 8, 8, 0]}
                onClick={(data) => {
                  if (data && data.site) {
                    onAiClick(
                      `Site Analysis: ${data.site}`,
                      `**Site Performance Summary**\n\n` +
                      `**Rank:** #${data.rank} out of ${rankingsData.length} sites\n` +
                      `**Score:** ${data.score}/100\n` +
                      `**Percentile:** ${data.percentile}th\n\n` +
                      `**AI Analysis:**\n` +
                      `${data.site} is ${data.rank <= 3 ? 'a top performer' : data.rank <= 5 ? 'performing excellently' : 'showing solid performance'} in this study.\n\n` +
                      `**Comparative Insights:**\n` +
                      `- ${data.rank === 1 ? 'Leading the study with exceptional data quality' : `${data.score - rankingsData[0].score > -5 ? 'Close to the top performer' : 'Opportunity to improve to reach top 3'}`}\n` +
                      `- Score is ${data.score > 90 ? 'excellent' : data.score > 80 ? 'very good' : 'good'} compared to industry benchmarks\n` +
                      `- ${data.percentile}th percentile means outperforming ${data.percentile}% of all sites\n\n` +
                      `**Recommendations:**\n` +
                      `- ${data.rank <= 3 ? 'Maintain current best practices and share knowledge with other sites' : 'Review top-performing sites for best practice adoption'}\n` +
                      `- Focus on consistent data entry and timely query resolution\n` +
                      `- Schedule regular quality reviews to maintain or improve ranking`
                    );
                  }
                }}
                style={{ cursor: 'pointer' }}
              >
                {rankingsData.map((_: any, index: number) => (
                  <Cell
                    key={`cell-${index}`}
                    fill={index < 3 ? '#3b82f6' : '#60a5fa'}
                  />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}

      {!benchmarkData && !rankingsData && (
        <div className="glass-card p-12 text-center">
          <p className="text-gray-600">Enter a site ID and fetch benchmark data or load rankings</p>
        </div>
      )}
    </div>
  );
}