import React, { useEffect, useMemo, useState } from 'react';
import {
  BrainCircuit, FlaskConical, ShieldCheck, BarChart3, Gauge, GraduationCap,
  ArrowUpRight, Database, Trash2, RefreshCcw, AlertTriangle, ChevronRight,
  Plus, CheckCircle2, LockKeyhole, Sparkles, Target, Info, BookOpen,
} from 'lucide-react';
import { api } from './api';

const fmt = v => v == null ? '—' : Number(v).toFixed(1);
const blank = { student_id:'', previous_score:'', attendance_rate:'', next_score:'' };

function Stat({ icon: Icon, title, value, subtitle }) {
  return <div className="p11-stat"><span className="p11-stat-icon"><Icon size={20}/></span>
    <div><small>{title}</small><strong>{value}</strong><p>{subtitle}</p></div></div>;
}

export default function PredictionPage({ students }) {
  const [data,setData] = useState(null);
  const [busy,setBusy] = useState(true);
  const [error,setError] = useState('');
  const [note,setNote] = useState('');
  const [mode,setMode] = useState('demo');
  const [previous,setPrevious] = useState('76');
  const [attendance,setAttendance] = useState('88');
  const [prediction,setPrediction] = useState(null);
  const [predicting,setPredicting] = useState(false);
  const [form,setForm] = useState(blank);
  const [saving,setSaving] = useState(false);
  const [removing,setRemoving] = useState(null);

  async function reload() {
    setBusy(true);setError('');
    try {setData(await api.mlOverview());}
    catch(e){setError(e.message || 'Could not load ML information');}
    finally {setBusy(false);}
  }
  useEffect(()=>{reload();},[]);
  const entries = data?.example_rows || [];
  const enabled = mode === 'demo' || Boolean(data?.ready);
  const title = mode === 'demo' ? 'Synthetic training mode' : 'CampusFlow history mode';
  const count = data?.examples ?? 0;

  async function runPrediction(e) {
    e.preventDefault();setPredicting(true);setPrediction(null);setNote('');setError('');
    try {setPrediction(await api.mlPredict({mode, previous_score:Number(previous), attendance_rate:Number(attendance)}));}
    catch(e){setError(e.message);}
    finally {setPredicting(false);}
  }

  async function addExample(e) {
    e.preventDefault();setSaving(true);setNote('');setError('');
    try {
      await api.mlAddExample({student_id:Number(form.student_id),previous_score:Number(form.previous_score),attendance_rate:Number(form.attendance_rate),next_score:Number(form.next_score)});
      setForm(blank);setPrediction(null);await reload();setNote('Historical outcome saved. Training readiness updated.');
    } catch(e){setError(e.message);} finally {setSaving(false);}
  }

  async function removeExample(id) {
    if(!window.confirm('Remove this historical example? This does not remove the student or their marks.'))return;
    setRemoving(id);setNote('');setError('');
    try {await api.mlDeleteExample(id);await reload();setPrediction(null);setNote('Historical example removed.');}
    catch(e){setError(e.message);} finally {setRemoving(null);}
  }

  return <div className="p11-page">
    <div className="p11-header"><div><div className="p11-eyebrow"><BrainCircuit size={15}/> CAMPUSFLOW INTELLIGENCE / PHASE 11</div>
      <h1>Performance prediction <Sparkles size={26}/></h1>
      <p>Explore how earlier results and attendance relate to a subsequent assessment score.</p>
    </div><div className="p11-local"><LockKeyhole size={16}/> Local machine learning</div></div>

    <section className="p11-hero" aria-label="Machine learning overview">
      <div className="p11-hero-copy"><span className="p11-pill"><FlaskConical size={13}/> EDUCATIONAL ML LAB</span>
        <h2>Turn academic history into<br/> <em>evidence-based insights.</em></h2>
        <p>Try a clearly labeled fictional-data demonstration, or record real historical outcomes to train your own local prediction model. Estimates are never official grades.</p>
        <div className="p11-hero-chips"><span><ShieldCheck size={14}/> Admin-only</span><span><Database size={14}/> SQLite-backed</span><span><BarChart3 size={14}/> Ridge regression</span></div>
      </div>
      <div className="p11-hero-art" aria-hidden="true"><div className="p11-glow"/><span className="p11-glass p11-glass-a">78.5 <small>estimated score</small></span><span className="p11-glass p11-glass-b"><span>70</span><i/><span>80</span><i/><span>90</span></span><span className="p11-orb"><BrainCircuit size={64} strokeWidth={1.45}/></span></div>
    </section>

    {error && <div className="p11-alert p11-alert-error" role="alert"><AlertTriangle size={17}/><span>{error}</span><button type="button" onClick={()=>setError('')}>Dismiss</button></div>}
    {note && <div className="p11-alert p11-alert-ok" role="status"><CheckCircle2 size={17}/>{note}</div>}
    <div className="p11-stats">
      <Stat icon={Database} title="Historical examples" value={busy?'…':count} subtitle={`Minimum ${data?.minimum_examples || 12} required`}/>
      <Stat icon={GraduationCap} title="Distinct students" value={busy?'…':data?.students ?? 0} subtitle={`Minimum ${data?.minimum_students || 4} required`}/>
      <Stat icon={Gauge} title="Real-data model" value={data?.ready?'Ready':'Not ready'} subtitle={data?.ready?'Historical model can run':'Use the demo meanwhile'}/>
    </div>

    <div className="p11-grid">
      <section className="p11-panel p11-scenario"><div className="p11-panel-header"><div><span className="p11-kicker">01 / EXPLORE</span><h2>Predict a scenario</h2><p>Enter two inputs and generate an illustrative next-score estimate.</p></div><span className="p11-icon-bg"><Target size={20}/></span></div>
        <div className="p11-mode" role="group" aria-label="Prediction data source"><button className={mode==='demo'?'p11-selected':''} onClick={()=>{setMode('demo');setPrediction(null);}} type="button"><FlaskConical size={16}/> Synthetic demo</button><button className={mode==='real'?'p11-selected':''} onClick={()=>{setMode('real');setPrediction(null);}} type="button"><Database size={16}/> Real records</button></div>
        <div className="p11-mode-note"><Info size={16}/><span>{mode==='demo'?'Demo trains on 84 generated, fictional examples. No actual student outcomes are used.':'Real mode uses only historical before-and-after examples you record below. No data is sent to an external AI service.'}</span></div>
        <form onSubmit={runPrediction} className="p11-form">
          <div className="p11-two"><label>Previous assessment score <small>0–100</small><input type="number" min="0" max="100" step="0.1" required value={previous} onChange={e=>setPrevious(e.target.value)} /></label>
            <label>Attendance rate <small>0–100%</small><input type="number" min="0" max="100" step="0.1" required value={attendance} onChange={e=>setAttendance(e.target.value)} /></label></div>
          <button disabled={!enabled || predicting || busy} className="p11-primary" type="submit"><BrainCircuit size={18}/>{predicting?'Calculating estimate…':'Generate estimate'}<ArrowUpRight size={17}/></button>
        </form>
        {!enabled && <div className="p11-locked"><LockKeyhole size={18}/><div><strong>More historical data needed</strong><p>{data?.requirements?.join(' ') || 'Add more examples below to unlock real-data estimates.'}</p></div></div>}
        {prediction && <div className="p11-output" aria-live="polite"><div className="p11-output-top"><span>{prediction.mode==='demo'?'FICTIONAL DATA ESTIMATE':'HISTORICAL DATA ESTIMATE'}</span><CheckCircle2 size={18}/></div><div className="p11-output-number">{fmt(prediction.estimated_next_score)}<small>/ 100</small></div><div className="p11-output-meter"><i style={{width:`${prediction.estimated_next_score}%`}}/></div><p>{prediction.disclaimer}</p><div className="p11-eval">Held-out MAE: <strong>{fmt(prediction.evaluation.mae)} points</strong> <span>·</span> Previous-score baseline: <strong>{fmt(prediction.evaluation.baseline_mae)} points</strong></div><small>MAE means average absolute error on a limited held-out sample, not guaranteed accuracy.</small></div>}
      </section>

      <section className="p11-panel p11-how"><div className="p11-panel-header"><div><span className="p11-kicker">02 / UNDERSTAND</span><h2>How the model learns</h2><p>Predictions require genuinely observed outcomes.</p></div><span className="p11-icon-bg"><BookOpen size={20}/></span></div>
        <div className="p11-steps">
          <div><span className="p11-step-n">01</span><div><strong>Previous assessment</strong><p>Record an earlier score for a student.</p></div><ChevronRight size={16}/></div>
          <div><span className="p11-step-n">02</span><div><strong>Attendance before next exam</strong><p>Use the student's attendance rate during that period.</p></div><ChevronRight size={16}/></div>
          <div><span className="p11-step-n">03</span><div><strong>Actual later score</strong><p>Enter the real result after the next assessment.</p></div><ChevronRight size={16}/></div>
          <div><span className="p11-step-n">04</span><div><strong>Train & evaluate</strong><p>A local Ridge model learns relationships and is checked on held-out students.</p></div><CheckCircle2 size={16}/></div>
        </div>
        <div className="p11-caution"><AlertTriangle size={18}/><div><b>For learning and planning only</b><p>Two features cannot account for every factor affecting a result. This tool must not be used to make consequential decisions about students.</p></div></div>
      </section>
    </div>

    <section className="p11-panel p11-records"><div className="p11-record-header"><div><span className="p11-kicker">03 / TRAIN</span><h2>Historical outcomes</h2><p>Only enter genuine before-and-after examples. A student's earlier result and subsequent actual result are different measurements.</p></div><button className="p11-refresh" type="button" onClick={reload} disabled={busy}><RefreshCcw size={16}/> Refresh</button></div>
      <form className="p11-record-form" onSubmit={addExample}><label>Student<select required value={form.student_id} onChange={e=>setForm({...form,student_id:e.target.value})}><option value="">Select student…</option>{students.map(s=><option key={s.id} value={s.id}>{s.name} (#{s.id})</option>)}</select></label>
        <label>Earlier score<input type="number" required min="0" max="100" step="0.1" placeholder="e.g. 72" value={form.previous_score} onChange={e=>setForm({...form,previous_score:e.target.value})}/></label>
        <label>Attendance %<input type="number" required min="0" max="100" step="0.1" placeholder="e.g. 85" value={form.attendance_rate} onChange={e=>setForm({...form,attendance_rate:e.target.value})}/></label>
        <label>Later actual score<input type="number" required min="0" max="100" step="0.1" placeholder="e.g. 79" value={form.next_score} onChange={e=>setForm({...form,next_score:e.target.value})}/></label>
        <button type="submit" className="p11-add" disabled={saving}><Plus size={18}/>{saving?'Saving…':'Add example'}</button></form>
      <div className="p11-table-wrap"><table className="p11-table"><thead><tr><th>STUDENT</th><th>EARLIER SCORE</th><th>ATTENDANCE</th><th>LATER SCORE</th><th>ADDED</th><th/></tr></thead><tbody>
        {entries.map(entry=><tr key={entry.id}><td><strong>{entry.student_name}</strong><span>#{entry.student_id}</span></td><td>{fmt(entry.previous_score)}</td><td>{fmt(entry.attendance_rate)}%</td><td className="p11-value">{fmt(entry.next_score)}</td><td>{entry.created_at?.slice(0,10)}</td><td><button type="button" aria-label={`Delete example ${entry.id}`} className="p11-delete" disabled={removing===entry.id} onClick={()=>removeExample(entry.id)}><Trash2 size={16}/></button></td></tr>)}
        {!entries.length && <tr><td className="p11-empty" colSpan="6"><Database size={25}/><strong>No historical examples yet</strong><span>Start by adding an earlier score and an actual later outcome, or explore Synthetic demo above.</span></td></tr>}
      </tbody></table></div>
      <div className="p11-record-foot"><span><ShieldCheck size={15}/> Records are stored in your local students.db.</span><span>{count} historical examples · {data?.students ?? 0} students</span></div>
    </section>
    <div className="p11-bottom"><span><LockKeyhole size={15}/> Admin-only predictions · No third-party data sharing · No automatic student grading</span></div>
  </div>;
}
