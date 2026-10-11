import React, { useEffect, useState } from 'react';
import { ArrowRight, BookOpen, CheckCircle2, GraduationCap, LockKeyhole, ShieldCheck, Sparkles, UsersRound, AlertCircle, Eye, EyeOff } from 'lucide-react';
import { api } from './api';

export default function AuthScreen({ onSuccess }) {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [setupNeeded, setSetupNeeded] = useState(false);
  useEffect(() => { api.setupStatus().then(r => setSetupNeeded(!r.configured)).catch(() => {}); }, []);

  async function submit(e) {
    e.preventDefault();
    setBusy(true);
    setError('');
    try {
      const data = await api.login(username.trim(), password);
      onSuccess(data.user);
    } catch (err) { setError(err.message); }
    finally { setBusy(false); }
  }

  return <div className="auth-shell">
    <div className="auth-story">
      <div className="auth-brand"><div className="auth-brand-mark"><GraduationCap size={23}/></div><b>campus<span>flow</span></b><small>ACADEMIC WORKSPACE</small></div>
      <div className="auth-story-content">
        <span className="auth-kicker"><Sparkles size={15}/> YOUR CAMPUS, ORGANIZED.</span>
        <h1>Better decisions.<br/><em>Brighter futures.</em></h1>
        <p>Manage students, track performance, and uncover meaningful academic insights from one beautifully connected workspace.</p>
        <div className="auth-feature-list">
          <span><span><UsersRound size={18}/></span><b>Student management</b><small>All your records in one place</small></span>
          <span><span><BookOpen size={18}/></span><b>Academic analytics</b><small>Live progress and attendance</small></span>
          <span><span><ShieldCheck size={18}/></span><b>Role-based access</b><small>Protected admin and teacher areas</small></span>
        </div>
      </div>
      <div className="auth-visual" aria-hidden="true"><div className="auth-chart-card"><div className="auth-chart-title"/><div className="auth-bars"><i/><i/><i/><i/><i/><i/><i/></div><div className="auth-chart-bottom"/></div><div className="auth-orbit orbit-one"/><div className="auth-orbit orbit-two"/><span className="auth-spark">✦</span></div>
      <div className="auth-story-foot">CAMPUSFLOW • BUILT FOR FOCUSED LEARNING</div>
    </div>
    <main className="auth-main">
      <div className="auth-login-card">
        <div className="auth-mini-lock"><LockKeyhole size={22}/></div>
        <span className="auth-overline">WELCOME BACK</span>
        <h2>Sign in to your workspace</h2>
        <p>Enter your CampusFlow account to continue.</p>
        {setupNeeded && <div className="auth-setup" role="note"><AlertCircle size={18}/><span>First time here? Create an admin from the <b>backend</b> terminal with <code>python create_admin.py</code>.</span></div>}
        {error && <div role="alert" className="auth-error"><AlertCircle size={18}/><span>{error}</span></div>}
        <form onSubmit={submit} className="auth-form">
          <label htmlFor="auth-username">Username</label>
          <input autoComplete="username" id="auth-username" placeholder="Enter username" value={username} onChange={e => setUsername(e.target.value)} required maxLength={32}/>
          <label htmlFor="auth-password">Password</label>
          <div className="auth-password-wrap"><input id="auth-password" type={showPassword?'text':'password'} autoComplete="current-password" placeholder="Enter password" value={password} onChange={e => setPassword(e.target.value)} required/><button type="button" aria-label={showPassword?'Hide password':'Show password'} onClick={() => setShowPassword(p => !p)}>{showPassword?<EyeOff size={18}/>:<Eye size={18}/>}</button></div>
          <button className="auth-submit" type="submit" disabled={busy}>{busy?'Signing in...':'Sign in to CampusFlow'} <ArrowRight size={19}/></button>
        </form>
        <div className="auth-security"><CheckCircle2 size={17}/> Accounts are protected with password hashing and expiring sessions.</div>
      </div>
      <div className="auth-main-foot">CampusFlow · Phase 8</div>
    </main>
  </div>;
}
