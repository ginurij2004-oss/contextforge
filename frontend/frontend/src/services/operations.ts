import api from "./api";


export interface OperationsDailyPoint {
  date: string;
  completed: number;
  failed: number;
  other: number;
}


export interface OperationsSummary {
  automations_total: number;
  automations_enabled: number;
  scheduled_automations: number;
  upcoming_runs: number;
  runs_total: number;
  runs_completed: number;
  runs_failed: number;
  runs_pending: number;
  success_rate: number;
  pending_actions: number;
  failed_actions: number;
  daily_runs: OperationsDailyPoint[];
}


export interface AutomationAuditLogItem {
  id: number;
  user_id: number;
  automation_id: number | null;
  action_request_id: number | null;
  event_type: string;
  status: string;
  message: string;
  details: Record<string, unknown>;
  created_at: string;
}


export interface OperationsHealth {
  status: string;
  database: string;
  scheduler: string;
  n8n_configured: boolean;
  checked_at: string;
}


export async function getOperationsSummary(): Promise<OperationsSummary> {
  const response = await api.get<OperationsSummary>(
    "/operations/summary"
  );
  return response.data;
}


export async function getAutomationAuditLogs(
  limit = 100
): Promise<AutomationAuditLogItem[]> {
  const response = await api.get<AutomationAuditLogItem[]>(
    "/operations/audit-logs",
    {
      params: { limit },
    }
  );
  return response.data;
}


export async function getOperationsHealth(): Promise<OperationsHealth> {
  const response = await api.get<OperationsHealth>(
    "/operations/health"
  );
  return response.data;
}
