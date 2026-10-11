import React, { useCallback, useEffect, useState } from 'react';
import { AlertCircle, CheckCircle2, LockKeyhole, Plus, RefreshCcw, ShieldCheck, UserCog, UsersRound } from 'lucide-react';
import { api } from './api';

export default function AccountsPage() {
  const [accounts, setAccounts] = useState([]);
  const [busy, setBusy] = useState(false);
  const [loading, setLoading] = useState(true);
  const [notice, setNotice] = useState('');
  const [error, setError] = useState('');
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const refresh = useCallback(async () => {
    try { setAccounts(await api.accounts());setError(''); }
    catch(e){setError(e.message);} finally {setLoading(false);}
  }, []);
  useEffect(() => {refresh();}, [refresh]);
  async function add(e) {
    e.preventDefault(); setBusy(true);setError('');setNotice('');
    try { await api.createTeacher({username:username.trim(),password});setUsername('');setPassword('');setNotice('Teacher account created. Share credentials privately.');await refresh(); }
    catch(e){setError(e.message);} finally {setBusy(false);}
  }
  async function toggle(a) {
    setBusy(true);setError('');setNotice('');
    try {await api.setAccountStatus(a.id,!a.active);setNotice(`${a.username} ${a.active?'disabled':'enabled'}.`);await refresh();}
    catch(e){setError(e.message);} finally {setBusy(false);}
  }
  return <div className="accounts-page">
    <div className="page-heading inner-page-heading"><div><div className="eyebrow"><span className="eyebrow-dot"/> ADMINISTRATION</div><h1>Team access</h1><p>Create teacher accounts and manage who can access the workspace.</p></div><button className="outline-btn" onClick={refresh}><RefreshCcw size={16}/> Refresh</button></div>
    {error && <div className="auth-error" role="alert"><AlertCircle size={17}/>{error}</div>}
    {notice && <div className="account-success" role="status"><CheckCircle2 size={17}/>{notice}</div>}
    <div className="accounts-grid">
      <div className="account-panel">
        <div className="account-panel-icon"><UserCog size={23}/></div>
        <h2>Add a teacher</h2><p>Teachers can view academic records and add marks or attendance, but cannot edit or delete students.</p>
        <form onSubmit={add} className="auth-form">
          <label htmlFor="teacher-username">Username</label><input id="teacher-username" value={username} required minLength={3} maxLength={32} pattern="[A-Za-z][A-Za-z0-9._-]{2,31}" title="Start with a letter; use letters, numbers, dots, underscores or hyphens" onChange={e=>setUsername(e.target.value)} placeholder="e.g. teacher.sara" autoComplete="off"/>
          <label htmlFor="teacher-password">Temporary password</label><input id="teacher-password" value={password} required type="password" minLength={12} maxLength={128} onChange={e=>setPassword(e.target.value)} placeholder="At least 12 characters" autoComplete="new-password"/>
          <button type="submit" className="primary-btn" disabled={busy}><Plus size={17}/> Create teacher account</button>
        </form>
        <div className="account-tip"><LockKeyhole size={17}/> Passwords are never shown again. Avoid reusing personal passwords.</div>
      </div>
      <div className="account-panel account-panel-list">
        <div className="account-panel-title"><div><span className="account-panel-icon"><UsersRound size={22}/></span><div><h2>Workspace users</h2><p>Account roles and active status</p></div></div><span className="account-total">{accounts.length} users</span></div>
        {loading ? <p>Loading accounts...</p> : <div className="account-users">{accounts.map(a=><div className="account-user" key={a.id}>
          <span className="account-avatar">{a.username.slice(0,2).toUpperCase()}</span><span className="account-user-data"><strong>{a.username}</strong><small><ShieldCheck size={12}/>{a.role==='admin'?'Administrator':'Teacher'} · {a.active?'Active':'Disabled'}</small></span>
          {a.role==='teacher' ? <button disabled={busy} type="button" className={a.active?'account-disable':'account-enable'} onClick={()=>toggle(a)}>{a.active?'Disable':'Enable'}</button>:<span className="account-owner">Owner</span>}
        </div>)}</div>}
      </div>
    </div>
  </div>;
}
