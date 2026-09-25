import api from "./api";


export type ActionType =
  | "email"
  | "calendar"
  | "reminder"
  | "webhook"
  | "notification";


export type ActionStatus =
  | "pending"
  | "approved"
  | "rejected"
  | "executing"
  | "completed"
  | "failed";


export interface ActionRequestItem {
  id: number;
  user_id: number;
  message_id: number | null;

  action_type: ActionType;
  status: ActionStatus;

  title: string;
  payload: Record<string, unknown>;

  error_message: string | null;

  created_at: string;
  updated_at: string;

  approved_at: string | null;
  rejected_at: string | null;
  executed_at: string | null;
}


export interface ActionCreateInput {
  action_type: ActionType;
  title: string;
  payload: Record<string, unknown>;
  message_id?: number | null;
}


export interface ActionUpdateInput {
  title?: string;
  payload?: Record<string, unknown>;
}


export async function getActions(
  status?: ActionStatus
): Promise<ActionRequestItem[]> {

  const response =
    await api.get<ActionRequestItem[]>(
      "/actions",
      {
        params:
          status
            ? {
                status,
              }
            : undefined,
      }
    );


  return response.data;
}


export async function getAction(
  actionId: number
): Promise<ActionRequestItem> {

  const response =
    await api.get<ActionRequestItem>(
      `/actions/${actionId}`
    );


  return response.data;
}


export async function createAction(
  data: ActionCreateInput
): Promise<ActionRequestItem> {

  const response =
    await api.post<ActionRequestItem>(
      "/actions",
      data
    );


  return response.data;
}


export async function updateAction(
  actionId: number,
  data: ActionUpdateInput
): Promise<ActionRequestItem> {

  const response =
    await api.patch<ActionRequestItem>(
      `/actions/${actionId}`,
      data
    );


  return response.data;
}


export async function approveAction(
  actionId: number
): Promise<ActionRequestItem> {

  const response =
    await api.post<ActionRequestItem>(
      `/actions/${actionId}/approve`
    );


  return response.data;
}


export async function rejectAction(
  actionId: number
): Promise<ActionRequestItem> {

  const response =
    await api.post<ActionRequestItem>(
      `/actions/${actionId}/reject`
    );


  return response.data;
}


export async function executeAction(
  actionId: number
): Promise<ActionRequestItem> {

  const response =
    await api.post<ActionRequestItem>(
      `/actions/${actionId}/execute`
    );


  return response.data;
}

export async function retryAction(
  actionId: number
): Promise<ActionRequestItem> {

  const response =
    await api.post<ActionRequestItem>(
      `/actions/${actionId}/retry`
    );

  return response.data;
}

