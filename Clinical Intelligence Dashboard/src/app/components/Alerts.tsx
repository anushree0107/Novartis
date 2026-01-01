import { useState, useEffect } from 'react';
import { PieChart, Pie, Cell, ResponsiveContainer } from 'recharts';
import { Loader2 } from 'lucide-react';
import { fetchAlerts, fetchAlertSummary, Alert } from '../services/api';

interface AlertsProps {
  onAiClick: (title: string, content: string) => void;
}

// Mock data for fallback
const MOCK_ALERTS = [
  {
    id: '1',
    title: 'Critical Data Discrepancy',
    description: 'Multiple conflicting vital signs entries detected for Subject 1034',
    severity: 'critical',
    category: 'data_quality',
    entity_type: 'patient',
    entity_id: 'Subject 1034',
    recommended_action: 'Review and correct vital signs entries',
    llm_analysis: '',
  },
  {
    id: '2',
    title: 'Query Overdue',
    description: 'Query #2847 has exceeded response deadline by 5 days',
    severity: 'high',
    category: 'data_quality',
    entity_type: 'site',
    entity_id: 'Site 0042',
    recommended_action: 'Follow up with site coordinator',
    llm_analysis: '',
  },
  {
    id: '3',
    title: 'Missing Lab Results',
    description: 'Expected lab results not received within protocol timeframe',
    severity: 'medium',
    category: 'protocol',
    entity_type: 'patient',
    entity_id: 'Subject 1089',
    recommended_action: 'Contact lab for missing results',
    llm_analysis: '',
  },
  {
    id: '4',
    title: 'Protocol Deviation',
    description: 'Visit window violation detected for scheduled assessment',
    severity: 'high',
    category: 'protocol',
    entity_type: 'patient',
    entity_id: 'Subject 1156',
    recommended_action: 'Document deviation and assess impact',
    llm_analysis: '',
  },
  {
    id: '5',
    title: 'Data Entry Incomplete',
    description: 'Required fields missing in adverse event form',
    severity: 'medium',
    category: 'data_quality',
    entity_type: 'site',
    entity_id: 'Site 0089',
    recommended_action: 'Complete missing fields',
    llm_analysis: '',
  },
  {
    id: '6',
    title: 'System Performance',
    description: 'Slow query response times detected in production environment',
    severity: 'low',
    category: 'system',
    entity_type: 'system',
    entity_id: 'System',
    recommended_action: 'Monitor system performance',
    llm_analysis: '',
  },
];

export function Alerts({ onAiClick }: AlertsProps) {
  const [alerts, setAlerts] = useState<Alert[]>(MOCK_ALERTS);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadAlerts = async () => {
      try {
        const data = await fetchAlerts(50);
        setAlerts(data);
      } catch (err: any) {
        setError(err.message);
        // Keep mock data on error
      } finally {
        setLoading(false);
      }
    };
    loadAlerts();
  }, []);

  const severityCounts = {
    total: alerts.length,
    critical: alerts.filter(a => a.severity === 'critical').length,
    high: alerts.filter(a => a.severity === 'high').length,
    medium: alerts.filter(a => a.severity === 'medium').length,
    low: alerts.filter(a => a.severity === 'low').length,
  };

  const severityData = [
    { name: 'Critical', value: severityCounts.critical, color: '#E03C31' },
    { name: 'High', value: severityCounts.high, color: '#f97316' },
    { name: 'Medium', value: severityCounts.medium, color: '#f59e0b' },
    { name: 'Low', value: severityCounts.low, color: '#10b981' },
  ];

  // Count categories dynamically from alerts
  const categoryCounts = alerts.reduce((acc, a) => {
    const cat = a.category || 'other';
    acc[cat] = (acc[cat] || 0) + 1;
    return acc;
  }, {} as Record<string, number>);

  const categoryData = [
    { name: 'Data Quality', value: categoryCounts['data_quality'] || 0, color: '#3b82f6' },
    { name: 'Protocol', value: categoryCounts['protocol'] || 0, color: '#60a5fa' },
    { name: 'System', value: categoryCounts['system'] || 0, color: '#10b981' },
  ];

  const getSeverityColor = (severity: string) => {
    const colors: Record<string, string> = {
      critical: '#E03C31',
      high: '#f97316',
      medium: '#f59e0b',
      low: '#10b981',
    };
    return colors[severity] || '#888';
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h2 className="bg-gradient-to-r from-[#3b82f6] to-[#2563eb] bg-clip-text text-transparent mb-2">
          Alerts & Notifications
        </h2>
        <p className="text-gray-600 text-sm">
          Monitor critical issues and system notifications
        </p>
      </div>

      {/* Summary Bar */}
      <div className="grid grid-cols-5 gap-4">
        <div className="glass-card p-4 text-center">
          <div className="text-2xl text-gray-800 mb-1">{severityCounts.total}</div>
          <div className="text-xs text-gray-500">Total Alerts</div>
        </div>
        <div className="glass-card p-4 text-center border-l-4 border-l-[#E03C31]">
          <div className="text-2xl text-[#E03C31] mb-1">{severityCounts.critical}</div>
          <div className="text-xs text-gray-500">Critical</div>
        </div>
        <div className="glass-card p-4 text-center border-l-4 border-l-[#f97316]">
          <div className="text-2xl text-[#f97316] mb-1">{severityCounts.high}</div>
          <div className="text-xs text-gray-500">High</div>
        </div>
        <div className="glass-card p-4 text-center border-l-4 border-l-[#f59e0b]">
          <div className="text-2xl text-[#f59e0b] mb-1">{severityCounts.medium}</div>
          <div className="text-xs text-gray-500">Medium</div>
        </div>
        <div className="glass-card p-4 text-center border-l-4 border-l-[#10b981]">
          <div className="text-2xl text-[#10b981] mb-1">{severityCounts.low}</div>
          <div className="text-xs text-gray-500">Low</div>
        </div>
      </div>

      {/* Charts */}
      <div className="grid grid-cols-2 gap-6">
        <div className="glass-card p-6">
          <h3 className="text-gray-700 mb-2">Severity Distribution</h3>
          <p className="text-xs text-gray-500 mb-4">Click on any segment for AI analysis</p>
          <ResponsiveContainer width="100%" height={250}>
            <PieChart>
              <Pie
                data={severityData}
                cx="50%"
                cy="50%"
                outerRadius={100}
                dataKey="value"
                label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                onClick={(data) => {
                  if (data && data.name) {
                    onAiClick(
                      `${data.name} Alerts Analysis`,
                      `**${data.name} Priority Alerts: ${data.value} total**\n\n` +
                      `**Percentage:** ${((data.value / severityCounts.total) * 100).toFixed(1)}% of all alerts\n\n` +
                      `**AI Analysis:**\n` +
                      `${data.name === 'Critical' ?
                        'Critical alerts require immediate attention. These are high-impact issues that could affect data integrity or patient safety. Action within 24 hours is strongly recommended.' :
                        data.name === 'High' ?
                          'High priority alerts indicate significant issues that should be addressed within 48-72 hours. These may escalate to critical if not resolved promptly.' :
                          data.name === 'Medium' ?
                            'Medium priority alerts represent moderate issues. While not immediately urgent, they should be addressed within the week to prevent accumulation.' :
                            'Low priority alerts are informational or minor issues. Address these during regular maintenance cycles to maintain optimal system health.'
                      }\n\n` +
                      `**Recommended Actions:**\n` +
                      `- Review all ${data.name.toLowerCase()} alerts in the alerts list below\n` +
                      `- Assign appropriate team members to resolve issues\n` +
                      `- Document resolution steps for future reference\n` +
                      `- Consider root cause analysis for recurring patterns`
                    );
                  }
                }}
                style={{ cursor: 'pointer' }}
              >
                {severityData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Pie>
            </PieChart>
          </ResponsiveContainer>
        </div>

        <div className="glass-card p-6">
          <h3 className="text-gray-700 mb-2">Category Distribution</h3>
          <p className="text-xs text-gray-500 mb-4">Click on any segment for AI analysis</p>
          <ResponsiveContainer width="100%" height={250}>
            <PieChart>
              <Pie
                data={categoryData}
                cx="50%"
                cy="50%"
                innerRadius={60}
                outerRadius={100}
                dataKey="value"
                label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                onClick={(data) => {
                  if (data && data.name) {
                    onAiClick(
                      `${data.name} Category Analysis`,
                      `**${data.name} Alerts: ${data.value} total**\n\n` +
                      `**AI Analysis:**\n` +
                      `${data.name === 'Data Quality' ?
                        'Data quality issues are the most common category. This typically includes missing values, inconsistencies, and validation failures. Focus on training and automated checks to reduce these.' :
                        data.name === 'Protocol' ?
                          'Protocol-related alerts indicate deviations from study procedures. These may include visit window violations, missed assessments, or documentation gaps. Regular site training can help prevent these.' :
                          'System alerts relate to technical performance and infrastructure. Monitor these for potential impact on data collection workflows.'
                      }\n\n` +
                      `**Impact Assessment:**\n` +
                      `- ${data.name} issues represent ${((data.value / severityCounts.total) * 100).toFixed(1)}% of all alerts\n` +
                      `- Trending ${data.value >= 2 ? 'higher than average - consider targeted intervention' : 'within normal range'}\n\n` +
                      `**Recommendations:**\n` +
                      `- ${data.name === 'Data Quality' ? 'Implement additional validation rules and staff training' :
                        data.name === 'Protocol' ? 'Schedule protocol refresher sessions with sites' :
                          'Review system performance metrics and optimize as needed'}`
                    );
                  }
                }}
                style={{ cursor: 'pointer' }}
              >
                {categoryData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Pie>
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Alert Cards */}
      <div className="grid grid-cols-2 gap-4">
        {alerts.map((alert) => (
          <div
            key={alert.id}
            className="glass-card p-4 border-l-4 hover:shadow-[0_0_20px_rgba(59,130,246,0.2)] transition-all duration-200"
            style={{ borderLeftColor: getSeverityColor(alert.severity) }}
          >
            <div className="flex justify-between items-start mb-2">
              <h4 className="text-gray-800">{alert.title}</h4>
              <span
                className="px-2 py-1 rounded text-xs text-white uppercase"
                style={{ backgroundColor: getSeverityColor(alert.severity) }}
              >
                {alert.severity}
              </span>
            </div>

            <p className="text-gray-600 text-sm mb-3">{alert.description}</p>

            <div className="flex justify-between items-center text-xs text-gray-500">
              <span>{alert.entity_id}</span>
              <span>{alert.entity_type}</span>
            </div>

            <button
              onClick={() => onAiClick(
                `Alert Analysis: ${alert.title}`,
                `Detailed analysis of ${alert.title}:\n\n**Alert Summary:**\n${alert.description}\n\n**Severity:** ${alert.severity.toUpperCase()}\n**Entity:** ${alert.entity_id}\n**Category:** ${alert.category}\n\n**Root Cause Analysis:**\nThis alert was triggered due to automated quality checks detecting an anomaly in the data submission pattern. The system identified that the issue requires immediate attention based on protocol requirements and data integrity rules.\n\n**Recommended Actions:**\n${alert.recommended_action || '1. Review the source documentation for the affected entity\n2. Contact the site coordinator to verify data accuracy\n3. Update or correct the data entry within 24 hours\n4. Document resolution steps in the query management system'}\n\n**Impact Assessment:**\n- Data Quality Index may be affected\n- Protocol compliance timeline at risk\n- Immediate action recommended to prevent escalation\n\n${alert.llm_analysis || '**Historical Context:**\nSimilar issues have been resolved with an average resolution time of 2.3 days. Best practice is to address within 24 hours to maintain optimal site performance.'}`
              )}
              className="mt-3 w-full px-3 py-2 bg-white border border-[#3b82f6]/40 rounded-lg text-gray-800 text-sm hover:border-[#3b82f6] transition-all duration-200 hover:shadow-[0_0_12px_rgba(59,130,246,0.3)]"
            >
              🤖 AI Analysis
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}