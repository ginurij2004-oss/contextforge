import api from "./api";


export interface AnalyticsOverview {
  total_requests: number;

  successful_requests: number;

  failed_requests: number;

  success_rate: number;

  average_latency_ms: number;

  total_input_tokens: number;

  total_output_tokens: number;

  total_tokens: number;

  chat_requests: number;

  document_requests: number;

  agent_requests: number;
}


export interface DailyAnalytics {
  date: string;

  requests: number;

  successful_requests: number;

  failed_requests: number;

  average_latency_ms: number;

  input_tokens: number;

  output_tokens: number;
}


export interface RecentAIRequest {
  id: number;

  model: string;

  prompt_version?: string | null;

  mode: string;

  latency_ms?: number | null;

  input_tokens?: number | null;

  output_tokens?: number | null;

  total_tokens: number;

  status: string;

  created_at: string;
}


export interface EvaluationRun {
  id: number;

  overall_score?: number | null;

  retrieval_hit_rate?: number | null;

  document_accuracy?: number | null;

  page_accuracy?: number | null;

  keyword_accuracy?: number | null;

  no_answer_accuracy?: number | null;

  average_latency_ms: number;

  rag_score_threshold?: number | null;

  rag_top_k?: number | null;

  rag_chunk_size?: number | null;

  rag_chunk_overlap?: number | null;

  created_at: string;
}


export interface AnalyticsDashboardData {
  overview: AnalyticsOverview;

  daily_activity: DailyAnalytics[];

  recent_requests: RecentAIRequest[];

  evaluation_runs: EvaluationRun[];
}


export const getAnalyticsDashboard =
  async (): Promise<
    AnalyticsDashboardData
  > => {

    const response =
      await api.get<
        AnalyticsDashboardData
      >(
        "/analytics/dashboard"
      );


    return response.data;
  };