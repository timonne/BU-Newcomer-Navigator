/**
 * Backend API client — the single place the frontend talks to the server.
 *
 * ADDED FOR BACKEND INTEGRATION. This file is new; it does not replace or
 * modify any existing UI component.
 *
 * Requests go to a relative path (`/api/...` by default) which Vite proxies
 * to the backend during development — see the `server.proxy` block added to
 * vite.config.ts. Keeping the API same-origin is what lets the backend's
 * httpOnly auth cookie work: a cross-origin cookie would need
 * SameSite=None + Secure, which is not possible over plain http://localhost.
 *
 * Every request sends `credentials: 'include'` so that cookie is carried.
 * The frontend never sees, stores, or handles the token itself.
 */

const API_BASE = (import.meta.env.VITE_API_BASE_URL || '/api').replace(/\/$/, '');

export interface ApiError {
  code: string;
  message: string;
}

export class ApiRequestError extends Error {
  code: string;
  status: number;

  constructor(status: number, code: string, message: string) {
    super(message);
    this.name = 'ApiRequestError';
    this.status = status;
    this.code = code;
  }
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    ...init,
    credentials: 'include',
    headers: {
      ...(init.body ? { 'Content-Type': 'application/json' } : {}),
      ...(init.headers || {}),
    },
  });

  if (response.status === 204) return undefined as T;

  const text = await response.text();
  const payload = text ? JSON.parse(text) : null;

  if (!response.ok) {
    // The backend always returns {error: {code, message}} — see
    // backend/app/core/errors.py.
    const err: ApiError = payload?.error || {
      code: 'UNKNOWN_ERROR',
      message: 'Something went wrong. Please try again.',
    };
    throw new ApiRequestError(response.status, err.code, err.message);
  }

  return payload as T;
}

export const api = {
  get: <T>(path: string) => request<T>(path),
  post: <T>(path: string, body?: unknown) =>
    request<T>(path, { method: 'POST', body: body === undefined ? undefined : JSON.stringify(body) }),
  patch: <T>(path: string, body?: unknown) =>
    request<T>(path, { method: 'PATCH', body: body === undefined ? undefined : JSON.stringify(body) }),
  delete: <T>(path: string) => request<T>(path, { method: 'DELETE' }),
};

/** Turns any thrown error into a message safe to show in the UI. */
export function errorMessage(error: unknown, fallback: string): string {
  if (error instanceof ApiRequestError) return error.message;
  if (error instanceof TypeError) {
    // fetch() rejects with TypeError when the server is unreachable.
    return 'Could not reach the server. Is the backend running on port 8000?';
  }
  return fallback;
}
