/**
 * Chatbot service — real backend implementation.
 *
 * INTEGRATION NOTE: `sendMessage(userMessage)` and the `ChatResponse` shape
 * are unchanged from the mock, so Chatbot.tsx needed no edits.
 *
 * The source priority (university knowledge base -> forum -> general
 * guidance) now happens entirely on the server; this file no longer contains
 * any retrieval or fallback logic of its own. `sourceType` still arrives as
 * 'university' | 'community' | 'general', matching the existing
 * ChatMessage type.
 *
 * Personalisation is also server-side: the greeting uses the authenticated
 * user's real first name, taken from their account rather than sent from the
 * browser. Nothing here passes a name.
 */
import type { ChatMessage } from '../types';
import { api, errorMessage } from './api';

export interface ChatResponse {
  content: string;
  sourceType: 'university' | 'community' | 'general';
  sourceRef?: ChatMessage['sourceRef'];
  conversationId?: string;
}

/**
 * Sends a message to Navi. `conversationId` is optional — pass the id
 * returned by a previous reply to continue the same stored conversation
 * (history is persisted for signed-in users only).
 */
export async function sendMessage(
  userMessage: string,
  conversationId?: string,
): Promise<ChatResponse> {
  try {
    return await api.post<ChatResponse>('/chat/messages', {
      message: userMessage,
      conversationId,
    });
  } catch (error) {
    // The chat UI expects a ChatResponse, not a thrown error, so a failure
    // is surfaced as a general-source message rather than a broken screen.
    return {
      content: errorMessage(error, 'I could not reach the assistant just now. Please try again.'),
      sourceType: 'general',
    };
  }
}

export interface ConversationSummary {
  id: string;
  title?: string;
  createdAt: string;
  updatedAt: string;
  messageCount: number;
}

export async function getConversations(): Promise<ConversationSummary[]> {
  try {
    return await api.get<ConversationSummary[]>('/chat/conversations');
  } catch {
    return []; // Not signed in, or no history yet.
  }
}

export interface StoredConversation {
  id: string;
  title?: string;
  createdAt: string;
  updatedAt: string;
  messages: {
    id: string;
    role: 'user' | 'assistant';
    content: string;
    sourceType?: string;
    sourceRef?: ChatMessage['sourceRef'];
    createdAt: string;
  }[];
}

export async function getConversation(id: string): Promise<StoredConversation | null> {
  try {
    return await api.get<StoredConversation>(`/chat/conversations/${encodeURIComponent(id)}`);
  } catch {
    return null;
  }
}

export async function deleteConversation(id: string): Promise<boolean> {
  try {
    await api.delete(`/chat/conversations/${encodeURIComponent(id)}`);
    return true;
  } catch {
    return false;
  }
}
