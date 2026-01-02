/**
 * API Service - Centralized API calls for SAGE-Flow backend
 */

const API_BASE_URL = (import.meta as any).env?.VITE_API_URL || 'http://localhost:8000';

// Generic fetch wrapper with error handling
async function fetchApi<T>(endpoint: string, options?: RequestInit): Promise<T> {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
        headers: {
            'Content-Type': 'application/json',
            ...options?.headers,
        },
        ...options,
    });

    if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: response.statusText }));
        throw new Error(error.detail || `API error: ${response.status}`);
    }

    // Handle text responses (for reports)
    const contentType = response.headers.get('content-type');
    if (contentType?.includes('text/plain')) {
        return (await response.text()) as unknown as T;
    }

    return response.json();
}

// ============ DQI API ============

export interface DQIMetric {
    metric: string;
    value: number;
    contribution: number;
    status: string;
}

export interface DQIResponse {
    entity_id: string;
    entity_type: string;
    score: number;
    grade: string;
    status: string;
    is_clean: boolean;
    breakdown: DQIMetric[];
    explanation?: string;
    recommendations: string[];
    top_issues: string[];
}

export async function fetchDQI(entityType: 'site' | 'patient' | 'study', entityId: string): Promise<DQIResponse> {
    return fetchApi<DQIResponse>(`/api/dqi/${entityType}/${entityId}`);
}

// ============ Analytics API ============

export interface BenchmarkResponse {
    site_id: string;
    overall_percentile: number;
    overall_performance: string;
    study_rank?: string;
    strengths: string[];
    weaknesses: string[];
    peer_insights: string;
    recommendations: string[];
}

export interface RankingEntry {
    entity_id: string;
    rank: number;
    total: number;
    value: number;
    percentile: number;
}

export interface RankingResponse {
    metric: string;
    entity_type: string;
    rankings: RankingEntry[];
    top_performers: RankingEntry[];
    bottom_performers: RankingEntry[];
}

export async function fetchBenchmark(siteId: string): Promise<BenchmarkResponse> {
    return fetchApi<BenchmarkResponse>(`/api/analytics/benchmark/site/${siteId}`);
}

export async function fetchRankings(metric: string = 'dqi_score', limit: number = 10): Promise<RankingResponse> {
    return fetchApi<RankingResponse>(`/api/analytics/rankings/sites?metric=${metric}&limit=${limit}`);
}

export async function fetchLeaderboard(entityType: string = 'site', topN: number = 10): Promise<any> {
    return fetchApi<any>(`/api/analytics/leaderboard?entity_type=${entityType}&top_n=${topN}`);
}

// ============ Alerts API ============

export interface Alert {
    id: string;
    title: string;
    description: string;
    severity: string;
    category: string;
    entity_type: string;
    entity_id: string;
    recommended_action: string;
    llm_analysis: string;
}

export interface AlertSummary {
    total_alerts: number;
    by_severity: Record<string, number>;
    by_category: Record<string, number>;
    top_alerts: any[];
}

export async function fetchAlerts(limit: number = 50): Promise<Alert[]> {
    return fetchApi<Alert[]>(`/api/alerts/?limit=${limit}`);
}

export async function fetchAlertSummary(): Promise<AlertSummary> {
    return fetchApi<AlertSummary>('/api/alerts/summary');
}

export async function fetchAlertsBySeverity(severity: string): Promise<Alert[]> {
    return fetchApi<Alert[]>(`/api/alerts/severity/${severity}`);
}

// ============ Query API ============

export interface QueryRequest {
    question: string;
    verbose?: boolean;
}

export interface QueryResponse {
    question: string;
    intent: string;
    answer: string;
    execution_order: string;
    timing: {
        routing: number;
        sql: number;
        graph: number;
        merge: number;
        total: number;
    };
    success: boolean;
}

export async function executeQuery(question: string): Promise<QueryResponse> {
    return fetchApi<QueryResponse>('/api/query/query', {
        method: 'POST',
        body: JSON.stringify({ question, verbose: false }),
    });
}

export async function getQueryStatus(): Promise<{ status: string; graph_nodes: number }> {
    return fetchApi('/api/query/status');
}

// ============ NEXUS Text-to-SQL API (Fast Mode) ============

export interface NexusQueryRequest {
    question: string;
    num_candidates?: number;
    num_unit_tests?: number;
    disable_unit_test?: boolean;
    execute?: boolean;
    explain?: boolean;
}

export interface NexusQueryResponse {
    success: boolean;
    question: string;
    sql: string;
    explanation?: string;
    execution_result?: Record<string, any>;
    metrics: {
        total_time: number;
        total_tokens?: number;
        pipeline_time?: number;
    };
    error?: string;
}

export interface NexusBatchResponse {
    results: NexusQueryResponse[];
    total_time: number;
    success_count: number;
    failure_count: number;
}

export async function executeNexusQuery(
    question: string,
    options?: Partial<NexusQueryRequest>
): Promise<NexusQueryResponse> {
    return fetchApi<NexusQueryResponse>('/api/nexus/query', {
        method: 'POST',
        body: JSON.stringify({
            question,
            num_candidates: options?.num_candidates ?? 3,
            num_unit_tests: options?.num_unit_tests ?? 5,
            disable_unit_test: options?.disable_unit_test ?? false,
            execute: options?.execute ?? true,
            explain: options?.explain ?? true,
        }),
    });
}

export async function executeNexusBatch(
    questions: string[],
    options?: { execute?: boolean; explain?: boolean }
): Promise<NexusBatchResponse> {
    return fetchApi<NexusBatchResponse>('/api/nexus/query/batch', {
        method: 'POST',
        body: JSON.stringify({
            questions,
            execute: options?.execute ?? true,
            explain: options?.explain ?? false,
        }),
    });
}

export async function getNexusHealth(): Promise<{ status: string; database_connected: boolean; pipeline_ready: boolean }> {
    return fetchApi('/api/nexus/health');
}

export async function getNexusSchema(): Promise<{ tables: string[]; schema_details: Record<string, any> }> {
    return fetchApi('/api/nexus/schema');
}

// ============ Actions API ============

export interface ActionResponse {
    action_id: string;
    action_type: string;
    status: string;
    message: string;
    output?: any;
    steps_executed: string[];
    execution_time_ms: number;
}

export interface AvailableAction {
    action: string;
    example: string;
}

export async function executeAction(action: string): Promise<ActionResponse> {
    return fetchApi<ActionResponse>('/api/actions/execute', {
        method: 'POST',
        body: JSON.stringify({ action }),
    });
}

export async function fetchAvailableActions(): Promise<AvailableAction[]> {
    return fetchApi<AvailableAction[]>('/api/actions/available');
}

export async function fetchAuditLog(limit: number = 50): Promise<any[]> {
    return fetchApi<any[]>(`/api/actions/audit-log?limit=${limit}`);
}

// ============ Reports API ============

export interface ReportMetadata {
    report_id: string;
    report_type: string;
    title: string;
    entity_type: string;
    entity_id: string;
    generated_at: string;
}

export async function generateSiteReport(siteId: string): Promise<string> {
    return fetchApi<string>(`/api/reports/site/${siteId}`);
}

export async function generateStudyReport(studyId: string): Promise<string> {
    return fetchApi<string>(`/api/reports/study/${studyId}`);
}

export async function generateWeeklyDigest(studyId?: string): Promise<string> {
    const params = studyId ? `?study_id=${studyId}` : '';
    return fetchApi<string>(`/api/reports/weekly${params}`);
}

export async function getSiteReportJson(siteId: string): Promise<any> {
    return fetchApi<any>(`/api/reports/site/${siteId}/json`);
}

// ============ Health Check ============

export async function checkHealth(): Promise<{ status: string }> {
    return fetchApi('/health');
}

export async function getApiInfo(): Promise<any> {
    return fetchApi('/');
}
