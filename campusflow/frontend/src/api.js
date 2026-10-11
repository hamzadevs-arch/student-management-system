const SESSION_KEY = 'campusflow_session';

export function clearSession() { window.sessionStorage.removeItem(SESSION_KEY); }
export function hasSession() { return Boolean(window.sessionStorage.getItem(SESSION_KEY)); }

export async function request(path, options = {}) {
  const token = window.sessionStorage.getItem(SESSION_KEY);
  let response;
  try {
    response = await fetch(`/api${path}`, {
      ...options,
      headers: {
        ...(options.body != null ? { 'Content-Type': 'application/json' } : {}),
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
        ...options.headers,
      },
    });
  } catch {
    throw new Error('Cannot reach FastAPI. Start the backend on port 8000.');
  }
  if (!response.ok) {
    let detail;
    try {
      const body = await response.json();
      detail = typeof body.detail === 'string' ? body.detail : (Array.isArray(body.detail) ? body.detail.map(x => x.msg).join(', ') : null);
    } catch { /* no JSON response */ }
    if (response.status === 401 && path !== '/auth/login') {
      clearSession();
      window.dispatchEvent(new Event('campusflow-session-expired'));
    }
    throw new Error(detail || `Request failed (${response.status})`);
  }
  return response.status === 204 ? null : response.json();
}

export const api = {
  setupStatus: () => request('/auth/setup-status'),
  login: async (username,password) => {
    const data = await request('/auth/login', {method:'POST',body:JSON.stringify({username,password})});
    window.sessionStorage.setItem(SESSION_KEY,data.access_token);
    return data;
  },
  me: () => request('/auth/me'),
  logout: async () => { try { await request('/auth/logout', {method:'POST'}); } finally { clearSession(); } },
  accounts: () => request('/accounts'),
  createTeacher: payload => request('/accounts',{method:'POST',body:JSON.stringify(payload)}),
  setAccountStatus: (id,active) => request(`/accounts/${id}/status`,{method:'PATCH',body:JSON.stringify({active})}),
  dashboard: () => request('/dashboard'),
  students: (search = '') => request(`/students?search=${encodeURIComponent(search)}`),
  marks: () => request('/marks'),
  attendance: () => request('/attendance'),
  createStudent: data => request('/students', { method: 'POST', body: JSON.stringify(data) }),
  updateStudent: (id, data) => request(`/students/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  deleteStudent: id => request(`/students/${id}`, { method: 'DELETE' }),
  saveMarks: data => request('/marks', { method: 'POST', body: JSON.stringify(data) }),
  saveAttendance: data => request('/attendance', { method: 'POST', body: JSON.stringify(data) }),
  exportStudents: async () => {
    const token = window.sessionStorage.getItem(SESSION_KEY);
    const res=await fetch('/api/reports/students.csv',{headers: token ? {Authorization:`Bearer ${token}`} : {}});
    if (res.status===401) {clearSession();window.dispatchEvent(new Event('campusflow-session-expired'));}
    if (!res.ok) throw new Error(`Export failed (${res.status})`);
    return res.blob();
  },
};
