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

// Phase 9: authenticated report endpoints. Teachers can see aggregated analytics,
// while administrator-only download endpoints are enforced on the server.
const reportParams = filters => {
  const args = new URLSearchParams();
  Object.entries(filters).forEach(([key,value]) => {if (value) args.set(key, value);});
  return args.toString();
};
api.reportAnalytics = filters => request(`/reports/analytics?${reportParams(filters)}`);
api.downloadReport = async (kind, filters, studentId='') => {
  const path = kind === 'pdf' ? '/reports/summary.pdf'
    : kind === 'csv' ? '/reports/summary.csv'
    : `/reports/student/${encodeURIComponent(studentId)}.pdf`;
  const filename = kind === 'pdf' ? 'campusflow-academic-report.pdf'
    : kind === 'csv' ? 'campusflow-program-summary.csv'
    : `campusflow-student-${studentId}.pdf`;
  const token = window.sessionStorage.getItem(SESSION_KEY);
  let response;
  try {response = await fetch(`/api${path}?${reportParams(filters)}`, {
    headers: token ? {Authorization:`Bearer ${token}`} : {}
  });} catch {throw new Error('Cannot reach FastAPI. Start the backend on port 8000.');}
  if (response.status === 401) {clearSession();window.dispatchEvent(new Event('campusflow-session-expired'));}
  if (!response.ok) {
    let msg = `Download failed (${response.status})`;
    try { const data=await response.json(); if (typeof data.detail === 'string') msg=data.detail; } catch {}
    throw new Error(msg);
  }
  return {blob: await response.blob(), filename};
};

// Phase 10: authenticated, read-only academic assistant.
api.assistantCapabilities = () => request('/assistant/capabilities');
api.askAssistant = (question,context_student_id=null) => request('/assistant/ask', {
  method: 'POST',
  body: JSON.stringify({ question, context_student_id }),
});


// Phase 11: local machine learning lab; endpoints require administrator access.
api.mlOverview = () => request('/ml/overview');
api.mlAddExample = payload => request('/ml/examples',{method:'POST',body:JSON.stringify(payload)});
api.mlDeleteExample = id => request(`/ml/examples/${id}`,{method:'DELETE'});
api.mlPredict = payload => request('/ml/predict',{method:'POST',body:JSON.stringify(payload)});

// Phase 13: authenticated multipart uploads and calendar/branding endpoints.
async function uploadForm(path, file) {
  const token = window.sessionStorage.getItem(SESSION_KEY);
  const payload = new FormData(); payload.append('file',file);
  let response;
  try {response = await fetch(`/api${path}`,{method:'POST',headers:token?{Authorization:`Bearer ${token}`}:{},body:payload});}
  catch {throw new Error('Cannot connect to the CampusFlow backend.');}
  if (response.status===401){clearSession();window.dispatchEvent(new Event('campusflow-session-expired'));}
  if (!response.ok){let msg=`Upload failed (${response.status})`;try{const data=await response.json();if(typeof data.detail==='string')msg=data.detail;}catch{}throw new Error(msg);}
  return response.json();
}
api.previewImport=file=>uploadForm('/import/students/preview',file);
api.commitImport=file=>uploadForm('/import/students/commit',file);
api.calendarEvents=(filters={})=>request(`/calendar?${new URLSearchParams(filters)}`);
api.createCalendarEvent=body=>request('/calendar',{method:'POST',body:JSON.stringify(body)});
api.updateCalendarEvent=(id,body)=>request(`/calendar/${id}`,{method:'PUT',body:JSON.stringify(body)});
api.deleteCalendarEvent=id=>request(`/calendar/${id}`,{method:'DELETE'});
api.branding=()=>request('/branding');
api.updateBranding=body=>request('/branding',{method:'PUT',body:JSON.stringify(body)});
api.uploadLogo=file=>uploadForm('/branding/logo',file);
api.removeLogo=()=>request('/branding/logo',{method:'DELETE'});
api.downloadLogo=async()=>{
  const token=window.sessionStorage.getItem(SESSION_KEY);
  const response=await fetch('/api/branding/logo',{headers:token?{Authorization:`Bearer ${token}`}:{}});
  if(!response.ok)throw new Error('Unable to load university logo');
  return response.blob();
};
