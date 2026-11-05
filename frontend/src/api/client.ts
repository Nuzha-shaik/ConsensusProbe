/**
 * API Client for ConsensusProbe
 * Automatically attaches Authorization: Bearer <token> when available.
 * On 401 Unauthorized, triggers session clearance.
 */

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export async function apiClient(endpoint: string, options: RequestInit = {}): Promise<Response> {
  const url = endpoint.startsWith('http') ? endpoint : `${API_BASE}${endpoint}`;
  const headers = new Headers(options.headers || {});

  const token = localStorage.getItem('cp_auth_token');
  if (token) {
    headers.set('Authorization', `Bearer ${token}`);
  }

  const response = await fetch(url, {
    ...options,
    headers,
  });

  if (response.status === 401) {
    console.warn('[API Client] 401 Unauthorized encountered. Clearing session.');
    localStorage.removeItem('cp_auth_token');
    localStorage.removeItem('cp_auth_user');
    if (typeof window !== 'undefined') {
      window.location.href = '/login';
    }
  }

  return response;
}
