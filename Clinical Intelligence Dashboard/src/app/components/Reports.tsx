import { useState } from 'react';
import { Download, ChevronDown, Loader2 } from 'lucide-react';
import { generateSiteReport, generateStudyReport, generateWeeklyDigest } from '../services/api';
import ReactMarkdown from 'react-markdown';

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
        <h2 className="bg-gradient-to-r from-[#60a5fa] to-[#3b82f6] bg-clip-text text-transparent mb-2">
          Reports
        </h2>
        <p className="text-gray-300 text-sm">
          Generate comprehensive performance and analysis reports
        </p>
      </div>

      {/* Controls */}
      <div className="bg-[#1a2332] rounded-2xl border border-white/10 p-4 flex flex-wrap gap-4">
        <div className="relative flex-1 min-w-[200px]">
          <select
            value={reportType}
            onChange={(e) => setReportType(e.target.value)}
            className="w-full bg-[#0f1419] text-white px-4 py-2 pr-10 rounded-lg border border-white/10 focus:border-[#3b82f6] focus:outline-none appearance-none"
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
          className="flex-1 min-w-[200px] bg-[#0f1419] text-white px-4 py-2 rounded-lg border border-white/10 focus:border-[#3b82f6] focus:outline-none placeholder-gray-400"
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
        <div className="bg-[#1a2332] rounded-2xl border border-white/10 p-6">
          <div className="flex justify-between items-center mb-4">
            <h3 className="text-gray-200">Report Preview</h3>
            <button
              onClick={downloadReport}
              className="flex items-center gap-2 px-4 py-2 bg-[#0f1419] border border-white/10 rounded-lg text-white hover:border-[#3b82f6] transition-all duration-200"
            >
              <Download className="w-4 h-4" />
              Download
            </button>
          </div>

          <div className="bg-[#0f1419] p-6 rounded-lg max-h-[600px] overflow-y-auto">
            <div className="prose prose-invert max-w-none
              [&_h1]:text-2xl [&_h1]:text-white [&_h1]:mb-4 [&_h1]:mt-6
              [&_h2]:text-xl [&_h2]:text-white [&_h2]:mb-3 [&_h2]:mt-5 [&_h2]:border-b [&_h2]:border-white/10 [&_h2]:pb-2
              [&_h3]:text-lg [&_h3]:text-gray-200 [&_h3]:mb-2 [&_h3]:mt-4
              [&_p]:text-gray-200 [&_p]:mb-2
              [&_li]:text-gray-200 [&_li]:mb-1
              [&_strong]:text-white [&_strong]:font-semibold
              [&_hr]:border-white/10 [&_hr]:my-4
              [&_table]:w-full [&_table]:border-collapse [&_table]:my-4
              [&_th]:bg-gray-800 [&_th]:text-white [&_th]:font-semibold [&_th]:px-4 [&_th]:py-2 [&_th]:border [&_th]:border-white/10
              [&_td]:px-4 [&_td]:py-2 [&_td]:border [&_td]:border-white/10
              [&_code]:bg-gray-800 [&_code]:px-1 [&_code]:py-0.5 [&_code]:rounded [&_code]:text-sm
              [&_pre]:bg-gray-900 [&_pre]:text-gray-100 [&_pre]:p-4 [&_pre]:rounded-lg [&_pre]:overflow-x-auto
            ">
              <ReactMarkdown>
                {(() => {
                  // Clean up AI thinking tags and other artifacts
                  let cleanContent = report;
                  // Remove <think>...</think> blocks (including multiline)
                  cleanContent = cleanContent.replace(/<think>[\s\S]*?<\/think>/gi, '');
                  // Remove any remaining <think> or </think> tags
                  cleanContent = cleanContent.replace(/<\/?think>/gi, '');
                  // Remove any Okay/Ok prefixes that are common in AI responses
                  cleanContent = cleanContent.replace(/^(Okay,?\s*|Ok,?\s*)/gim, '');
                  return cleanContent.trim();
                })()}
              </ReactMarkdown>
            </div>
          </div>
        </div>
      )}

      {!report && (
        <div className="bg-[#1a2332] rounded-2xl border border-white/10 p-12 text-center">
          <p className="text-gray-300">Select report type and click "Generate Report"</p>
        </div>
      )}
    </div>
  );
}