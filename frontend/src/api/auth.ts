import { apiRequest, tokenStorageKey } from './client';

export async function login(username: string, password: string) {
  const result = await apiRequest<{ access_token: string; token_type: string }>('/auth/login', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ username, password })
  });
  localStorage.setItem(tokenStorageKey, result.access_token);
  return result;
}

export function logout() {
  localStorage.removeItem(tokenStorageKey);
}

export function isLoggedIn() {
  return Boolean(localStorage.getItem(tokenStorageKey));
}

