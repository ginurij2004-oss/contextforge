import api from "./api";


export type ChatMode =
  | "chat"
  | "documents"
  | "agent";


export interface Conversation {
  id: number;
  user_id: number;
  title: string;
  created_at: string;
}


export interface ChatSource {
  document_id?: number | null;
  filename: string;
  page?: number | null;
  score?: number | null;
}


export interface ActionItem {
  title: string;
  description: string;

  priority:
    | "low"
    | "medium"
    | "high";
}


export interface ChatMessage {
  id: number;

  conversation_id: number;

  role:
    | "user"
    | "assistant";

  content: string;

  model?: string | null;

  input_tokens?: number | null;

  output_tokens?: number | null;

  latency_ms?: number | null;

  created_at: string;


  // ----------------------------------
  // Persistent Mode Metadata
  // ----------------------------------

  mode: ChatMode;

  document_id?: number | null;

  confidence?:
    | "low"
    | "medium"
    | "high"
    | null;


  // ----------------------------------
  // RAG / Agent Metadata
  // ----------------------------------

  sources: ChatSource[];

  used_tools: string[];

  action_items: ActionItem[];
}


interface SendMessageResponse {
  user_message: ChatMessage;
  assistant_message: ChatMessage;
}


// ==========================================================
// Create Conversation
// ==========================================================

export const createConversation =
  async (): Promise<Conversation> => {

    const response =
      await api.post<Conversation>(
        "/conversations",
        {
          title: "New Conversation",
        }
      );

    return response.data;
  };


// ==========================================================
// Get Conversations
// ==========================================================

export const getConversations =
  async (): Promise<Conversation[]> => {

    const response =
      await api.get<Conversation[]>(
        "/conversations"
      );

    return response.data;
  };


// ==========================================================
// Get Messages
// ==========================================================

export const getMessages =
  async (
    conversationId: number
  ): Promise<ChatMessage[]> => {

    const response =
      await api.get<ChatMessage[]>(
        `/conversations/${conversationId}/messages`
      );

    return response.data;
  };


// ==========================================================
// Send Message
// ==========================================================

export const sendChatMessage =
  async (
    conversationId: number,
    content: string,
    mode: ChatMode,
    documentId?: number | null
  ): Promise<SendMessageResponse> => {

    const response =
      await api.post<SendMessageResponse>(
        `/conversations/${conversationId}/messages`,
        {
          content,
          mode,
          document_id:
            documentId ?? null,
        }
      );

    return response.data;
  };

// ==========================================================
// Rename Conversation
// ==========================================================

export async function renameConversation(
  conversationId: number,
  title: string
): Promise<Conversation> {

  const response =
    await api.patch<Conversation>(
      `/conversations/${conversationId}`,
      {
        title,
      }
    );

  return response.data;
}


// ==========================================================
// Delete Conversation
// ==========================================================

export async function deleteConversation(
  conversationId: number
): Promise<void> {

  await api.delete(
    `/conversations/${conversationId}`
  );

}