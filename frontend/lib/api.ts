import { ApiResponse } from "@/types/api";

function getCsrfToken(): string | null {
  if (typeof document === "undefined") return null;
  const match = document.cookie.match(/(?:^|;\s*)(?:giftledger_csrf|gl_csrf)=([^;]+)/);
  return match ? decodeURIComponent(match[1]) : null;
}

export async function apiRequest<T = any>(
  endpoint: string,
  options: RequestInit = {}
): Promise<ApiResponse<T>> {
  const url = endpoint.startsWith("/") ? endpoint : `/${endpoint}`;
  const headers = new Headers(options.headers || {});

  if (!headers.has("Content-Type") && !(options.body instanceof FormData)) {
    headers.set("Content-Type", "application/json");
  }

  const method = (options.method || "GET").toUpperCase();
  if (["POST", "PATCH", "PUT", "DELETE"].includes(method)) {
    const csrf = getCsrfToken();
    if (csrf && !headers.has("X-CSRF-Token")) {
      headers.set("X-CSRF-Token", csrf);
    }
  }

  const response = await fetch(url, {
    ...options,
    headers,
    credentials: "include",
  });

  if (response.status === 204) {
    return { success: true, data: {} as T };
  }

  const contentType = response.headers.get("content-type");
  if (contentType && contentType.includes("application/json")) {
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data?.error?.message || "An error occurred");
    }
    return data;
  }

  if (!response.ok) {
    throw new Error(`Request failed with status ${response.status}`);
  }

  return { success: true, data: {} as T };
}

export const api = {
  get: <T = any>(url: string, headers?: Record<string, string>) =>
    apiRequest<T>(url, { method: "GET", headers }),

  post: <T = any>(url: string, body?: any, headers?: Record<string, string>) =>
    apiRequest<T>(url, {
      method: "POST",
      body: body ? JSON.stringify(body) : undefined,
      headers,
    }),

  patch: <T = any>(url: string, body?: any, headers?: Record<string, string>) =>
    apiRequest<T>(url, {
      method: "PATCH",
      body: body ? JSON.stringify(body) : undefined,
      headers,
    }),

  delete: <T = any>(url: string, headers?: Record<string, string>) =>
    apiRequest<T>(url, { method: "DELETE", headers }),
};
