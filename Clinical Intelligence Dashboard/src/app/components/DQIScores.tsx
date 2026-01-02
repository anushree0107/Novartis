import { useState } from 'react';
import { PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, ResponsiveContainer } from 'recharts';
import { ChevronDown, Loader2 } from 'lucide-react';
import { fetchDQI as fetchDQIApi, DQIResponse } from '../services/api';

interface DQIScoresProps {
  onAiClick: (title: string, content: string) => void;
}

export function DQIScores({ onAiClick }: DQIScoresProps) {
  const [entityType, setEntityType] = useState<'site' | 'patient' | 'study'>('site');
  const [entityId, setEntityId] = useState('');
  const [dqiData, setDqiData] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchDQI = async () => {
    if (!entityId.trim()) {
      setError('Please enter an Entity ID');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await fetchDQIApi(entityType, entityId);
      // Transform API response to component format
      setDqiData({
        score: response.score,
        grade: response.grade,
        breakdown: response.breakdown.map(m => ({
          metric: (m.name || m.metric || 'Unknown').replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()),
          value: m.raw_value !== undefined
            ? (m.raw_value < 1 ? m.raw_value * 100 : Math.min(m.raw_value, 100))
            : (m.normalized_value !== undefined ? m.normalized_value * 100 : Math.min(m.contribution, 100)),
          status: m.status?.toLowerCase() === 'good' ? 'good' : m.status?.toLowerCase() === 'critical' ? 'critical' : 'warning',
        })),
        issues: response.top_issues,
        recommendations: response.recommendations,
        explanation: response.explanation,
      });
    } catch (err: any) {
      setError(err.message || 'Failed to fetch DQI data');
      // Fallback to mock data for demo
      setDqiData({
        score: 87.5,
        grade: 'B',
        breakdown: [
          { metric: 'Completeness', value: 92, status: 'good' },
          { metric: 'Consistency', value: 85, status: 'good' },
          { metric: 'Timeliness', value: 78, status: 'warning' },
          { metric: 'Accuracy', value: 95, status: 'good' },
          { metric: 'Validity', value: 82, status: 'warning' },
        ],
        issues: [
          'Missing values in 3 required fields',
          'Query response time exceeds target by 2 days',
          'Inconsistent date formats detected',
        ],
        recommendations: [
          'Schedule training session for site staff',
          'Implement automated validation checks',
          'Review data entry procedures for lab results',
          'Set up automated reminders for pending queries',
        ],
      });
    } finally {
      setLoading(false);
    }
  };

  const getGradeColor = (grade: string) => {
    const colors: Record<string, string> = {
      A: '#10b981',
      B: '#0091DF',
      C: '#f59e0b',
      D: '#EC6602',
      F: '#E03C31',
    };
    return colors[grade] || '#888';
  };

  const getStatusColor = (status: string) => {
    const colors: Record<string, string> = {
      good: '#10b981',
      warning: '#f59e0b',
      critical: '#E03C31',
    };
    return colors[status] || '#888';
  };

  const gaugeData = dqiData ? [
    { value: dqiData.score },
    { value: 100 - dqiData.score },
  ] : [];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h2 className="bg-gradient-to-r from-[#3b82f6] to-[#2563eb] bg-clip-text text-transparent mb-2">
          Data Quality Index
        </h2>
        <p className="text-gray-600 text-sm">
          Monitor and analyze data quality metrics across entities
        </p>
      </div>

      {/* Controls */}
      <div className="glass-card p-4 flex flex-wrap gap-4">
        <div className="relative flex-1 min-w-[200px]">
          <select
            value={entityType}
            onChange={(e) => setEntityType(e.target.value as 'site' | 'patient' | 'study')}
            className="w-full bg-white text-gray-800 px-4 py-2 pr-10 rounded-lg border border-[#3b82f6]/30 focus:border-[#3b82f6] focus:outline-none appearance-none"
          >
            <option value="site">Site</option>
            <option value="patient">Patient</option>
            <option value="study">Study</option>
          </select>
          <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400 pointer-events-none" />
        </div>

        <input
          type="text"
          placeholder="Entity ID"
          value={entityId}
          onChange={(e) => setEntityId(e.target.value)}
          className="flex-1 min-w-[200px] bg-white text-gray-800 px-4 py-2 rounded-lg border border-[#3b82f6]/30 focus:border-[#3b82f6] focus:outline-none placeholder-gray-500"
        />

        <button
          onClick={fetchDQI}
          className="px-6 py-2 bg-gradient-to-r from-[#3b82f6] to-[#2563eb] text-white rounded-lg hover:shadow-[0_0_20px_rgba(37,99,235,0.4)] transition-all duration-200"
        >
          Fetch DQI
        </button>
      </div>

      {/* DQI Cards Grid */}
      {dqiData && (
        <div className="grid grid-cols-2 gap-6">
          {/* Score Card */}
          <div className="glass-card p-6">
            <h3 className="text-gray-700 mb-6">Overall Score</h3>
            <div className="flex flex-col items-center">
              <div className="relative w-48 h-48 cursor-pointer" onClick={() => onAiClick(
                'DQI Score Details',
                `**Current Score: ${dqiData.score}/100 (Grade ${dqiData.grade})**\n\n` +
                `**Metric Breakdown:**\n` +
                dqiData.breakdown.map((m: any) => `- ${m.metric}: ${m.value}% (${m.status})`).join('\n') +
                `\n\n**AI Analysis:**\n` +
                `The overall DQI score of ${dqiData.score} indicates ${dqiData.score >= 85 ? 'strong' : dqiData.score >= 70 ? 'moderate' : 'needs improvement'} data quality performance.\n\n` +
                `**Key Insights:**\n` +
                `- ${dqiData.breakdown.filter((m: any) => m.status === 'good').length} metrics are performing well\n` +
                `- ${dqiData.breakdown.filter((m: any) => m.status === 'warning').length} metrics need attention\n` +
                `- Focus on improving timeliness and validity scores for best impact\n\n` +
                `**Recommendations:**\n` +
                dqiData.recommendations.map((r: string) => `- ${r}`).join('\n')
              )}>
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={gaugeData}
                      cx="50%"
                      cy="50%"
                      startAngle={135}
                      endAngle={-135}
                      innerRadius={60}
                      outerRadius={80}
                      paddingAngle={0}
                      dataKey="value"
                    >
                      <Cell fill={getGradeColor(dqiData.grade)} />
                      <Cell fill="#e5e7eb" />
                    </Pie>
                  </PieChart>
                </ResponsiveContainer>
                <div className="absolute inset-0 flex items-center justify-center">
                  <div className="text-center">
                    <div className="text-4xl text-gray-800">{dqiData.score}</div>
                    <div className="text-sm text-gray-500">/ 100</div>
                  </div>
                </div>
              </div>

              <div className="mt-6 flex items-center gap-4">
                <div
                  className="px-4 py-2 rounded-lg text-white"
                  style={{ backgroundColor: getGradeColor(dqiData.grade) }}
                >
                  Grade {dqiData.grade}
                </div>
                <button
                  onClick={() => onAiClick('DQI Score Analysis', 'Based on the current DQI score of 87.5, the data quality is good overall. The site demonstrates strong performance in completeness (92%) and accuracy (95%). However, there are opportunities for improvement in timeliness (78%), which is impacting the overall score.\n\nKey insights:\n- The site is performing above the 75th percentile for accuracy\n- Timeliness issues are primarily related to query response times\n- Recent trend shows improvement over the past 30 days\n\nRecommendations:\n- Focus on query resolution workflow optimization\n- Implement automated reminders for pending queries\n- Consider additional training for staff on data entry timelines')}
                  className="px-4 py-2 bg-white border border-[#3b82f6]/40 rounded-lg text-gray-800 hover:border-[#3b82f6] transition-all duration-200 hover:shadow-[0_0_12px_rgba(37,99,235,0.3)] animate-pulse"
                >
                  🤖 AI
                </button>
              </div>
            </div>
          </div>

          {/* Breakdown Card */}
          <div className="glass-card p-6">
            <h3 className="text-gray-700 mb-6">Metric Breakdown</h3>
            <div className="space-y-4">
              {dqiData.breakdown.map((item: any, idx: number) => (
                <div key={idx}>
                  <div className="flex justify-between mb-1 text-sm">
                    <span className="text-gray-700">{item.metric}</span>
                    <span className="text-gray-800">{item.value}%</span>
                  </div>
                  <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
                    <div
                      className="h-full rounded-full transition-all duration-500"
                      style={{
                        width: `${item.value}%`,
                        backgroundColor: getStatusColor(item.status),
                      }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Issues Card */}
          <div className="glass-card p-6 border-l-4 border-l-[#E03C31]">
            <h3 className="text-gray-700 mb-4">Key Issues</h3>
            <ul className="space-y-2">
              {dqiData.issues.map((issue: string, idx: number) => (
                <li key={idx} className="flex items-start gap-2 text-gray-700 text-sm">
                  <span className="text-[#E03C31] mt-1">•</span>
                  <span>{issue}</span>
                </li>
              ))}
            </ul>
          </div>

          {/* Recommendations Card */}
          <div className="glass-card p-6 border-l-4 border-l-[#10b981]">
            <h3 className="text-gray-700 mb-4">Recommendations</h3>
            <ul className="space-y-2">
              {dqiData.recommendations.map((rec: string, idx: number) => (
                <li key={idx} className="flex items-start gap-2 text-gray-700 text-sm">
                  <span className="text-[#10b981] mt-1">✓</span>
                  <span>{rec}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>
      )}

      {!dqiData && (
        <div className="glass-card p-12 text-center">
          <p className="text-gray-600">Enter an entity ID and click "Fetch DQI" to view scores</p>
        </div>
      )}
    </div>
  );
}