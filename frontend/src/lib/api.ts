import { DatasetProfile } from './types';

const rawApiBase = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000';
export const API_BASE = rawApiBase.replace(/\/+$/, '');

export async function checkBackendHealth(): Promise<{ status: string; service: string } | null> {
  try {
    const res = await fetch(`${API_BASE}/health`, { method: 'GET' });
    if (!res.ok) return null;
    return await res.json();
  } catch (error) {
    console.error('Health check failed:', error);
    return null;
  }
}

export async function fetchDatasetProfile(): Promise<DatasetProfile | null> {
  try {
    const res = await fetch(`${API_BASE}/api/dataset/profile`, { method: 'GET' });
    if (!res.ok) return null;
    return await res.json();
  } catch (error) {
    console.error('Failed to fetch dataset profile:', error);
    return null;
  }
}

export async function fetchThreadHistory(threadId: string) {
  try {
    const res = await fetch(`${API_BASE}/api/threads/${threadId}`, { method: 'GET' });
    if (!res.ok) return null;
    return await res.json();
  } catch (error) {
    console.error(`Failed to fetch thread ${threadId}:`, error);
    return null;
  }
}

export async function streamChatQuery({
  query,
  threadId,
  onSession,
  onNodeUpdate,
  onFinalResult,
  onError,
}: {
  query: string;
  threadId: string;
  onSession?: (data: any) => void;
  onNodeUpdate?: (data: any) => void;
  onFinalResult?: (data: any) => void;
  onError?: (err: any) => void;
}) {
  try {
    const response = await fetch(`${API_BASE}/api/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ query, thread_id: threadId }),
    });

    if (!response.ok || !response.body) {
      const errorBody = await response.text().catch(() => '');
      throw new Error(`Chat API error (${response.status}): ${errorBody || response.statusText}`);
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder('utf-8');
    let buffer = '';
    let currentEvent = 'message';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop() || '';

      for (const line of lines) {
        const trimmed = line.trim();
        if (trimmed === '') {
          currentEvent = 'message';
          continue;
        }

        if (trimmed.startsWith('event:')) {
          currentEvent = trimmed.replace('event:', '').trim();
        } else if (trimmed.startsWith('data:')) {
          const rawData = trimmed.replace('data:', '').trim();
          try {
            const parsed = JSON.parse(rawData);
            if (currentEvent === 'session' && onSession) {
              onSession(parsed);
            } else if (currentEvent === 'node_update' && onNodeUpdate) {
              onNodeUpdate(parsed);
            } else if (currentEvent === 'final_result' && onFinalResult) {
              onFinalResult(parsed);
            } else if (currentEvent === 'error' && onError) {
              onError(parsed);
            }
          } catch (e) {
            console.error('Failed to parse SSE JSON payload:', rawData, e);
          }
        }
      }
    }
  } catch (error: any) {
    console.error('Error in SSE stream:', error);
    if (onError) onError({ error: error?.message || String(error) });
  }
}
