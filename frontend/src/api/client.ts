import { message } from 'antd';

const API_BASE = import.meta.env.VITE_API_BASE ?? 'http://localhost:8000/api';

export const tokenStorageKey = 'student-portrait-token';

function getHeaders(extra?: HeadersInit): HeadersInit {
  const token = localStorage.getItem(tokenStorageKey);
  return {
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...extra
  };
}

export async function apiRequest<T>(path: string, options: RequestInit = {}): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: getHeaders(options.headers)
  });

  if (!response.ok) {
    const body = await response.text();
    message.error(body || '请求失败');
    throw new Error(body || 'Request failed');
  }

  return response.json() as Promise<T>;
}

