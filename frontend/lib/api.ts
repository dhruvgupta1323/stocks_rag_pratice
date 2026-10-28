const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000/api/v1";

export interface StockSearchResult {
  instrument_id: string;
  company_id: string;
  name: string;
  symbol: string;
  exchange: string;
  isin?: string;
  sector: string;
  industry: string;
  last_price?: number;
  currency: string;
}

export interface QuoteRead {
  id?: string;
  instrument_id: string;
  symbol: string;
  exchange: string;
  last_price: number;
  open: number;
  high: number;
  low: number;
  previous_close: number;
  change: number;
  change_percent: number;
  volume: number;
  provider: string;
  market_timestamp: string;
  fetched_at: string;
  data_status: string;
  currency: string;
}

export interface StockOverview {
  instrument_id: string;
  company_id: string;
  name: string;
  symbol: string;
  exchange: string;
  sector: string;
  industry: string;
  description?: string;
  quote: QuoteRead;
  high_52w?: number;
  low_52w?: number;
  market_cap_crores?: number;
  pe_ratio?: number;
  pb_ratio?: number;
  data_status: string;
  last_updated: string;
}

export interface PriceBar {
  timestamp: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export interface HistoricalBarsResponse {
  instrument_id: string;
  symbol: string;
  exchange: string;
  interval: string;
  bars: PriceBar[];
  provider: string;
  data_status: string;
}

export interface FinancialMetric {
  id: string;
  company_id: string;
  metric_name: string;
  value: number;
  unit: string;
  currency: string;
  reporting_period: string;
  period_type: string;
  reported_at?: string;
}

export interface CompanyFinancials {
  company_id: string;
  company_name: string;
  symbol: string;
  annual_metrics: FinancialMetric[];
  quarterly_metrics: FinancialMetric[];
  ttm_metrics: FinancialMetric[];
  calculated_ratios: Record<string, any>;
}

export interface ResearchArticle {
  id: string;
  company_id?: string;
  source_type: string;
  title: string;
  publisher: string;
  url: string;
  published_at: string;
  retrieved_at: string;
  processing_status: string;
  licensing_notes?: string;
}

export interface StockNewsResponse {
  symbol: string;
  company_name: string;
  total_articles: number;
  articles: ResearchArticle[];
}

export interface Citation {
  source_id: string;
  title: string;
  publisher: string;
  url: string;
  published_at: string;
  claim?: string;
}

export interface AskQuestionResponse {
  conversation_id: string;
  question: string;
  direct_answer: string;
  supporting_facts: string[];
  explanations?: string;
  citations: Citation[];
  data_timestamps: Record<string, any>;
  limitations: string[];
  data_status: string;
  sufficiency: string;
}

export interface EvaluationResult {
  id: string;
  run_id: string;
  question_id: string;
  category: string;
  question_text: string;
  expected_answer: string;
  actual_answer: string;
  retrieved_source_ids: string[];
  metric_results: Record<string, any>;
  failure_reason?: string;
  latency_ms: number;
}

export interface EvaluationRun {
  id: string;
  dataset_version: string;
  model_version: string;
  retrieval_configuration: Record<string, any>;
  started_at: string;
  completed_at?: string;
  status: string;
  summary_metrics: Record<string, any>;
  results?: EvaluationResult[];
}

// API functions
export async function searchStocks(query: string, exchange?: string): Promise<StockSearchResult[]> {
  const params = new URLSearchParams({ q: query });
  if (exchange) params.append("exchange", exchange);
  const res = await fetch(`${API_BASE}/stocks/search?${params.toString()}`);
  if (!res.ok) throw new Error("Failed to search stocks");
  return res.json();
}

export async function getStockOverview(instrumentId: string): Promise<StockOverview> {
  const res = await fetch(`${API_BASE}/stocks/${instrumentId}/overview`);
  if (!res.ok) throw new Error("Failed to load stock overview");
  return res.json();
}

export async function getHistoricalBars(
  instrumentId: string,
  days = 90,
  interval = "1d"
): Promise<HistoricalBarsResponse> {
  const res = await fetch(`${API_BASE}/stocks/${instrumentId}/history?days=${days}&interval=${interval}`);
  if (!res.ok) throw new Error("Failed to load historical bars");
  return res.json();
}

export async function getStockFinancials(instrumentId: string): Promise<CompanyFinancials> {
  const res = await fetch(`${API_BASE}/stocks/${instrumentId}/financials`);
  if (!res.ok) throw new Error("Failed to load financials");
  return res.json();
}

export async function getStockNews(instrumentId: string, limit = 15): Promise<StockNewsResponse> {
  const res = await fetch(`${API_BASE}/stocks/${instrumentId}/news?limit=${limit}`);
  if (!res.ok) throw new Error("Failed to load news");
  return res.json();
}

export async function getStockReport(instrumentId: string): Promise<any> {
  const res = await fetch(`${API_BASE}/stocks/${instrumentId}/report`);
  if (!res.ok) throw new Error("Failed to generate research report");
  return res.json();
}

export async function askQuestion(
  question: string,
  instrumentId?: string,
  conversationId?: string
): Promise<AskQuestionResponse> {
  const res = await fetch(`${API_BASE}/research/ask`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      question,
      instrument_id: instrumentId,
      conversation_id: conversationId,
    }),
  });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.message || "Failed to process research question");
  }
  return res.json();
}

export async function runEvaluation(): Promise<EvaluationRun> {
  const res = await fetch(`${API_BASE}/evaluation/run`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({}),
  });
  if (!res.ok) throw new Error("Failed to trigger benchmark evaluation");
  return res.json();
}

export async function getEvaluationRuns(): Promise<EvaluationRun[]> {
  const res = await fetch(`${API_BASE}/evaluation/runs`);
  if (!res.ok) throw new Error("Failed to fetch evaluation runs");
  return res.json();
}

export async function getEvaluationRun(runId: string): Promise<EvaluationRun> {
  const res = await fetch(`${API_BASE}/evaluation/runs/${runId}`);
  if (!res.ok) throw new Error("Failed to fetch evaluation run details");
  return res.json();
}

