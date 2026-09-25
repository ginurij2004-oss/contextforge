import api from "./api";


export type AutomationActionType =
  | "email"
  | "calendar"
  | "webhook";


export type AutomationTriggerType =
  | "manual"
  | "once"
  | "daily"
  | "weekdays"
  | "weekly"
  | "interval";


export interface AutomationItem {
  id: number;
  user_id: number;

  name: string;
  description: string | null;

  trigger_type: AutomationTriggerType;
  schedule: Record<string, unknown> | null;
  action_type: AutomationActionType;

  config: Record<string, unknown>;

  is_enabled: boolean;
  requires_approval: boolean;

  next_run_at: string | null;
  last_triggered_at: string | null;

  created_at: string;
  updated_at: string;
}


export interface AutomationRunItem {
  id: number;
  automation_id: number;
  automation_name: string;

  user_id: number;
  action_request_id: number | null;

  action_type: AutomationActionType;

  status: string;
  trigger_source: "manual" | "schedule" | string;
  scheduled_for: string | null;
  error_message: string | null;

  created_at: string;
  started_at: string | null;
  completed_at: string | null;
}


export interface AutomationCreateInput {
  name: string;
  description?: string | null;

  trigger_type: AutomationTriggerType;
  schedule?: Record<string, unknown> | null;
  action_type: AutomationActionType;

  config: Record<string, unknown>;

  is_enabled: boolean;
  requires_approval: boolean;
}


export interface AutomationUpdateInput {
  name?: string;
  description?: string | null;
  trigger_type?: AutomationTriggerType;
  schedule?: Record<string, unknown> | null;
  config?: Record<string, unknown>;
  is_enabled?: boolean;
  requires_approval?: boolean;
}


export async function getAutomations(
  enabled?: boolean
): Promise<AutomationItem[]> {

  const response =
    await api.get<AutomationItem[]>(
      "/automations",
      {
        params:
          enabled === undefined
            ? undefined
            : { enabled },
      }
    );

  return response.data;
}


export async function getUpcomingAutomations(
  limit = 20
): Promise<AutomationItem[]> {

  const response =
    await api.get<AutomationItem[]>(
      "/automations/upcoming",
      {
        params: { limit },
      }
    );

  return response.data;
}


export async function createAutomation(
  data: AutomationCreateInput
): Promise<AutomationItem> {

  const response =
    await api.post<AutomationItem>(
      "/automations",
      data
    );

  return response.data;
}


export async function updateAutomation(
  automationId: number,
  data: AutomationUpdateInput
): Promise<AutomationItem> {

  const response =
    await api.patch<AutomationItem>(
      `/automations/${automationId}`,
      data
    );

  return response.data;
}


export async function deleteAutomation(
  automationId: number
): Promise<void> {

  await api.delete(
    `/automations/${automationId}`
  );
}


export async function runAutomation(
  automationId: number
): Promise<AutomationRunItem> {

  const response =
    await api.post<AutomationRunItem>(
      `/automations/${automationId}/run`
    );

  return response.data;
}


export async function getAutomationRuns(
  limit = 50
): Promise<AutomationRunItem[]> {

  const response =
    await api.get<AutomationRunItem[]>(
      "/automations/runs",
      {
        params: { limit },
      }
    );

  return response.data;
}


export async function getAutomationRunsForAutomation(
  automationId: number,
  limit = 50
): Promise<AutomationRunItem[]> {

  const response =
    await api.get<AutomationRunItem[]>(
      `/automations/${automationId}/runs`,
      {
        params: { limit },
      }
    );

  return response.data;
}
