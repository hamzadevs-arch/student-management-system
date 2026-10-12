import React, { useState } from 'react';
import { UploadCloud, FileSpreadsheet, ShieldCheck, CheckCircle2, AlertCircle, Download, ArrowRight, Users, Info, LoaderCircle } from 'lucide-react';
import { api } from './api';

function makeTemplate() {
  const text = 'id,name,age,email,course\n1001,Example Student,20,student@example.com,Computer Science\n';
  const link = document.createElement('a');
  const url = URL.createObjectURL(new Blob([text], {type:'text/csv;charset=utf-8'}));
  link.href=url;link.download='campusflow-import-template.csv';link.click();
  setTimeout(()=>URL.revokeObjectURL(url),1000);
}

export default function ImportPage({ onImported }) {
  const [file,setFile] = useState(null);
  const [preview,setPreview] = useState(null);
  const [result,setResult] = useState(null);
  const [error,setError] = useState('');
  const [busy,setBusy] = useState(false);
  function choose(value) {setFile(value);setPreview(null);setResult(null);setError('');}
  async function inspect() {
    if(!file)return;
    setBusy(true);setError('');
    try { setPreview(await api.previewImport(file)); }
    catch(err){setError(err.message);}finally{setBusy(false);}
  }
  async function commit() {
    if(!file||!preview||preview.invalid_count)return;
    setBusy(true);setError('');
    try {const r=await api.commitImport(file);setResult(r);setPreview(null);await onImported();}
    catch(err){setError(err.message);}finally{setBusy(false);}
  }
  return <div className="cf13-page">
    <header className="cf13-page-heading"><div><span className="eyebrow"><span className="eyebrow-dot"/> STUDENT DATA / IMPORT CENTER</span><h1>Import students <span className="cf13-gradient">with confidence</span></h1><p>Bring your existing roster into CampusFlow with a preview, row validation and safe duplicate handling.</p></div><button className="cf13-button-light" onClick={makeTemplate}><Download size={17}/> Download template</button></header>
    <div className="cf13-stat-strip"><div><FileSpreadsheet size={22}/><span><b>CSV + Excel</b><small>.csv and .xlsx files</small></span></div><div><ShieldCheck size={22}/><span><b>No accidental overwrites</b><small>Existing student IDs are skipped</small></span></div><div><Users size={22}/><span><b>Up to 1,500 records</b><small>Validated before import</small></span></div></div>
    <div className="cf13-import-grid">
      <section className="cf13-panel cf13-panel-pad"><div className="cf13-panel-heading"><span className="cf13-icon-box"><UploadCloud size={20}/></span><div><h2>Upload student roster</h2><p>Start by selecting a file from your computer.</p></div></div>
        <label className="cf13-dropzone"><input type="file" accept=".csv,.xlsx" onChange={e=>choose(e.target.files?.[0]||null)}/><span className="cf13-drop-icon"><UploadCloud size={28}/></span><b>{file ? file.name : 'Choose a CSV or Excel file'}</b><span>{file ? `${Math.ceil(file.size/1024)} KB selected` : 'Click here to browse · Maximum 3 MB'}</span></label>
        <button disabled={!file||busy} className="cf13-button-primary cf13-block" onClick={inspect}>{busy?<LoaderCircle size={18} className="spinning"/>:<ArrowRight size={18}/>} {busy?'Validating records...':'Preview & validate file'}</button>
        {error&&<div role="alert" className="cf13-alert error"><AlertCircle size={19}/>{error}</div>}
        {result&&<div role="status" className="cf13-alert success"><CheckCircle2 size={19}/><span><b>{result.imported} student(s) imported.</b> {result.skipped_existing} existing ID(s) skipped. Your dashboard is ready to refresh.</span></div>}
      </section>
      <aside className="cf13-panel cf13-panel-pad cf13-instructions"><div className="cf13-panel-heading"><span className="cf13-icon-box purple"><Info size={20}/></span><div><h2>Prepare your file</h2><p>The first row must contain these columns.</p></div></div>
        <div className="cf13-code-head">id, name, age, email, course</div>
        <div className="cf13-step"><b>01</b><span>Use a unique numeric <strong>id</strong> for every student.</span></div><div className="cf13-step"><b>02</b><span>Include a full <strong>name</strong>, <strong>age</strong>, and program in <strong>course</strong>.</span></div><div className="cf13-step"><b>03</b><span>The email field may be blank, but the header must be present.</span></div><div className="cf13-step"><b>04</b><span>Preview first, fix highlighted rows, then confirm the import.</span></div>
        <div className="cf13-mini-note"><ShieldCheck size={16}/> Import is restricted to administrator accounts and does not change existing students.</div>
      </aside>
    </div>
    {preview&&<section className="cf13-panel cf13-preview"><div className="cf13-preview-head"><div><h2>Validation preview</h2><p>{preview.total_rows} records checked. No changes have been made to your database.</p></div><div className="cf13-preview-badges"><span className="cf13-tag green">{preview.ready_count} ready</span><span className="cf13-tag neutral">{preview.existing_count} already exist</span><span className={`cf13-tag ${preview.invalid_count?'red':'neutral'}`}>{preview.invalid_count} invalid</span></div></div>
      {preview.errors?.length>0&&<div className="cf13-errors" role="alert">{preview.errors.map((e,i)=><p key={i}>Row {e.row}: {e.message}</p>)}{preview.invalid_count>preview.errors.length&&<p>Additional validation errors are not shown.</p>}</div>}
      <div className="cf13-table-scroll"><table className="cf13-table"><thead><tr><th>ID</th><th>STUDENT NAME</th><th>AGE</th><th>EMAIL</th><th>PROGRAM</th><th>RESULT</th></tr></thead><tbody>{preview.preview.map((r,i)=><tr key={i}><td>#{r.id}</td><td><strong>{r.name}</strong></td><td>{r.age}</td><td>{r.email||'—'}</td><td>{r.course}</td><td><span className={`cf13-tag ${r.status==='ready'?'green':'neutral'}`}>{r.status==='ready'?'Ready':'Already exists'}</span></td></tr>)}</tbody></table></div>
      <div className="cf13-preview-foot"><p>{preview.invalid_count?'Fix the invalid rows before importing.': 'Confirm to save new students and skip existing IDs.'}</p><button className="cf13-button-primary" onClick={commit} disabled={busy||preview.invalid_count>0||preview.ready_count===0}><CheckCircle2 size={17}/>{busy?'Importing...':`Import ${preview.ready_count} students`}</button></div>
    </section>}
  </div>;
}
