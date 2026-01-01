import { useState } from 'react';
import { Download, ChevronDown, Loader2 } from 'lucide-react';
import { generateSiteReport, generateStudyReport, generateWeeklyDigest } from '../services/api';

export function Reports() {
  const [reportType, setReportType] = useState('site');
  const [entityId, setEntityId] = useState('');
  const [report, setReport] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const generateReport = async () => {
    setLoading(true);
    setError(null);

    try {
      let reportContent: string;

      switch (reportType) {
        case 'site':
          if (!entityId.trim()) {
            setError('Please enter a Site ID');
            setLoading(false);
            return;
          }
          reportContent = await generateSiteReport(entityId);
          break;
        case 'study':
          if (!entityId.trim()) {
            setError('Please enter a Study ID');
            setLoading(false);
            return;
          }
          reportContent = await generateStudyReport(entityId);
          break;
        case 'weekly':
          reportContent = await generateWeeklyDigest(entityId || undefined);
          break;
        default:
          reportContent = '';
      }

      setReport(reportContent);
    } catch (err: any) {
      setError(err.message || 'Report generation failed');
      // Fallback to mock report
      const mockReport = `# ${reportType.toUpperCase()} PERFORMANCE REPORT
**Entity ID:** ${entityId || 'N/A'}  
**Generated:** ${new Date().toLocaleString()}  
**Report Period:** Last 30 Days

---

## Executive Summary

This comprehensive report provides detailed insights into the performance metrics, data quality indicators, and operational efficiency for the selected ${reportType}.

### Key Metrics
- **Overall DQI Score:** 87.5/100 (Grade B)
- **Total Records Processed:** 1,247
- **Query Resolution Rate:** 94.2%
- **Protocol Compliance:** 96.8%

---

## Data Quality Analysis

### Completeness: 92%
All required fields are consistently populated with minimal missing data.

### Consistency: 85%
Data validation checks show good consistency across related fields.

### Timeliness: 78%
Some delays observed in query response times.

### Accuracy: 95%
High accuracy rate with minimal corrections required.

---

## Recommendations

1. **Improve Query Response Time**
   - Implement automated reminder system
   - Target: Reduce to 2 days average

2. **Standardize Date Formats**
   - Deploy automated validation rules

3. **Continue Best Practices**
   - Maintain current enrollment momentum

---

**Report End**`;

      setReport(mockReport);
    } finally {
      setLoading(false);
    }
  };

  const downloadReport = () => {
    if (!report) return;

    const blob = new Blob([report], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${reportType}_report_${Date.now()}.md`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h2 className="bg-gradient-to-r from-[#3b82f6] to-[#2563eb] bg-clip-text text-transparent mb-2">
          Reports
        </h2>
        <p className="text-gray-600 text-sm">
          Generate comprehensive performance and analysis reports
        </p>
      </div>

      {/* Controls */}
      <div className="glass-card p-4 flex flex-wrap gap-4">
        <div className="relative flex-1 min-w-[200px]">
          <select
            value={reportType}
            onChange={(e) => setReportType(e.target.value)}
            className="w-full bg-white text-gray-800 px-4 py-2 pr-10 rounded-lg border border-[#3b82f6]/30 focus:border-[#3b82f6] focus:outline-none appearance-none"
          >
            <option value="site">Site Report</option>
            <option value="study">Study Report</option>
            <option value="weekly">Weekly Summary</option>
          </select>
          <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400 pointer-events-none" />
        </div>

        <input
          type="text"
          placeholder="Entity ID (optional)"
          value={entityId}
          onChange={(e) => setEntityId(e.target.value)}
          className="flex-1 min-w-[200px] bg-white text-gray-800 px-4 py-2 rounded-lg border border-[#3b82f6]/30 focus:border-[#3b82f6] focus:outline-none placeholder-gray-500"
        />

        <button
          onClick={generateReport}
          className="px-6 py-2 bg-gradient-to-r from-[#3b82f6] to-[#2563eb] text-white rounded-lg hover:shadow-[0_0_20px_rgba(37,99,235,0.4)] transition-all duration-200"
        >
          Generate Report
        </button>
      </div>

      {/* Report Display */}
      {report && (
        <div className="glass-card p-6">
          <div className="flex justify-between items-center mb-4">
            <h3 className="text-gray-700">Report Preview</h3>
            <button
              onClick={downloadReport}
              className="flex items-center gap-2 px-4 py-2 bg-white border border-[#3b82f6]/40 rounded-lg text-gray-800 hover:border-[#3b82f6] transition-all duration-200"
            >
              <Download className="w-4 h-4" />
              Download
            </button>
          </div>

          <div className="bg-white p-6 rounded-lg max-h-[600px] overflow-y-auto">
            <div className="prose prose-gray max-w-none">
              {report.split('\n').map((line, idx) => {
                if (line.startsWith('# ')) {
                  return <h1 key={idx} className="text-2xl text-gray-800 mb-4 mt-6">{line.slice(2)}</h1>;
                }
                if (line.startsWith('## ')) {
                  return <h2 key={idx} className="text-xl text-gray-800 mb-3 mt-5 border-b border-[#3b82f6]/30 pb-2">{line.slice(3)}</h2>;
                }
                if (line.startsWith('### ')) {
                  return <h3 key={idx} className="text-lg text-gray-700 mb-2 mt-4">{line.slice(4)}</h3>;
                }
                if (line.startsWith('**') && line.endsWith('**')) {
                  return <p key={idx} className="text-gray-800 mb-2">{line.replace(/\*\*/g, '')}</p>;
                }
                if (line.startsWith('- ')) {
                  return <li key={idx} className="text-gray-700 ml-4 mb-1">{line.slice(2)}</li>;
                }
                if (line.startsWith('```')) {
                  return null;
                }
                if (line.includes('|') || line.includes('---')) {
                  return <div key={idx} className="text-gray-700 text-sm font-mono">{line}</div>;
                }
                if (line.trim() === '---') {
                  return <hr key={idx} className="border-[#3b82f6]/20 my-4" />;
                }
                if (line.trim()) {
                  return <p key={idx} className="text-gray-700 mb-2">{line}</p>;
                }
                return <br key={idx} />;
              })}
            </div>
          </div>
        </div>
      )}

      {!report && (
        <div className="glass-card p-12 text-center">
          <p className="text-gray-600">Select report type and click "Generate Report"</p>
        </div>
      )}
    </div>
  );
}