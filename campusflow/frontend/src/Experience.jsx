import React, { useEffect, useMemo, useRef, useState } from 'react';
import {
  Search, ArrowRight, GraduationCap, LayoutDashboard, ClipboardCheck, BookOpen,
  ChartNoAxesCombined, Sparkles, BrainCircuit, ShieldCheck, Settings, X, Mail,
  BookMarked, CalendarDays, UserRound, AlertCircle, CheckCircle2, Plus,
  TrendingUp, CircleHelp, Keyboard, PanelRightClose, BellRing, FileUp, CalendarRange, FileBadge2
} from 'lucide-react';

const searchPages = [
  {key:'overview', label:'Overview', icon:LayoutDashboard, hint:'Dashboard and key metrics'},
  {key:'students', label:'Student directory', icon:GraduationCap, hint:'Browse and manage students'},
  {key:'attendance', label:'Attendance', icon:ClipboardCheck, hint:'Presence and absence records'},
  {key:'grades', label:'Grades & marks', icon:BookOpen, hint:'Assessment results'},
  {key:'reports', label:'Reports', icon:ChartNoAxesCombined, hint:'PDFs and academic analytics'},
  {key:'calendar', label:'Academic calendar', icon:CalendarRange, hint:'Exams, deadlines, university holidays'},
  {key:'import', label:'Import students', icon:FileUp, hint:'Bulk upload CSV and Excel', adminOnly:true},
  {key:'branding', label:'University branding', icon:FileBadge2, hint:'PDF report headers and logo', adminOnly:true},
  {key:'assistant', label:'AI assistant', icon:Sparkles, hint:'Ask academic questions'},
  {key:'prediction', label:'ML predictions', icon:BrainCircuit, hint:'Experimental ML tools', adminOnly:true},
  {key:'accounts', label:'Team access', icon:ShieldCheck, hint:'Administrator accounts', adminOnly:true},
  {key:'settings', label:'Preferences', icon:Settings, hint:'Workspace appearance and shortcuts'},
];

function matchingSearchItems(query, students, isAdmin) {
  const q = query.trim().toLocaleLowerCase();
  const pages = searchPages.filter(page => !page.adminOnly || isAdmin)
    .filter(page => !q || `${page.label} ${page.hint}`.toLocaleLowerCase().includes(q))
    .map(page => ({...page, type:'page', id:`page-${page.key}`}));
  const names = students.filter(student => !q || `${student.name} ${student.id} ${student.course || ''}`.toLocaleLowerCase().includes(q))
    .slice(0, 8).map(student => ({id:`student-${student.id}`, type:'student', label:student.name, hint:`Student #${student.id} · ${student.course || 'No program'}`, icon:UserRound, student}));
  return [...pages, ...names].slice(0, 14);
}

export function CommandPalette({ students, isAdmin, onClose, onPage, onStudent }) {
  const [query, setQuery] = useState('');
  const [cursor, setCursor] = useState(0);
  const inputRef = useRef(null);
  const results = useMemo(() => matchingSearchItems(query,students,isAdmin),[query,students,isAdmin]);
  useEffect(() => { inputRef.current?.focus(); }, []);
  useEffect(() => { setCursor(0); }, [query]);
  function pick(item) {if (!item) return; item.type==='page' ? onPage(item.key) : onStudent(item.student); onClose();}
  function keyHandler(e) {
    if (e.key==='Escape') {e.preventDefault();onClose();}
    if (e.key==='ArrowDown') {e.preventDefault();setCursor(c=>Math.min(results.length-1,c+1));}
    if (e.key==='ArrowUp') {e.preventDefault();setCursor(c=>Math.max(0,c-1));}
    if (e.key==='Enter') {e.preventDefault();pick(results[cursor]);}
  }
  return <div className="cf12-command-overlay" onMouseDown={e=>{if(e.target===e.currentTarget)onClose();}}>
    <section className="cf12-command" role="dialog" aria-modal="true" aria-label="Search CampusFlow">
      <div className="cf12-command-input"><Search size={21}/><input ref={inputRef} placeholder="Search students, pages and tools..." aria-label="Search student records and navigation" value={query} onChange={e=>setQuery(e.target.value)} onKeyDown={keyHandler}/><button onClick={onClose} aria-label="Close search"><X size={18}/></button></div>
      <div className="cf12-command-results" role="listbox" aria-label="Search results">
        {results.length ? results.map((item,i) => <button type="button" key={item.id} role="option" aria-selected={i===cursor} className={`cf12-command-result ${i===cursor?'selected':''}`} onMouseEnter={()=>setCursor(i)} onClick={()=>pick(item)}><span className="cf12-command-result-icon"><item.icon size={18}/></span><span><b>{item.label}</b><small>{item.hint}</small></span><ArrowRight size={17}/></button>) : <div className="cf12-command-empty"><Search size={24}/><b>No matches</b><span>Try a student name, ID or a page name.</span></div>}
      </div>
      <div className="cf12-command-footer"><span><kbd>↑</kbd><kbd>↓</kbd> navigate</span><span><kbd>Enter</kbd> select</span><span><kbd>Esc</kbd> close</span></div>
    </section>
  </div>;
}

const showPercent = num => num == null ? 'Not recorded' : `${Number(num).toFixed(1).replace(/\.0$/,'')}%`;

export function StudentProfile({ student, marks, attendance, onClose, canManage, onMarks, onAttendance }) {
  const entries = marks.filter(m=>Number(m.student_id)===Number(student.id));
  const present = attendance.filter(r=>Number(r.student_id)===Number(student.id)).sort((a,b)=>String(b.date).localeCompare(String(a.date)));
  const score = entries.length ? entries.reduce((n,m)=>n+Number(m.marks),0)/entries.length : null;
  const [tab,setTab] = useState('marks');
  useEffect(()=>{const handler=e=>{if(e.key==='Escape')onClose();};window.addEventListener('keydown',handler);return ()=>window.removeEventListener('keydown',handler);},[onClose]);
  return <div className="cf12-drawer-backdrop" onMouseDown={e=>{if(e.target===e.currentTarget)onClose();}}>
    <aside role="dialog" aria-modal="true" aria-label={`Profile for ${student.name}`} className="cf12-profile-drawer">
      <header className="cf12-drawer-top"><span>STUDENT PROFILE</span><button onClick={onClose} aria-label="Close student profile"><X size={20}/></button></header>
      <div className="cf12-profile-content">
        <div className="cf12-profile-hero"><div className="cf12-profile-avatar">{student.name.split(/\s+/).slice(0,2).map(x=>x[0]).join('').toUpperCase()}</div><h2>{student.name}</h2><p>Student ID #{student.id}</p><span className="cf12-profile-program"><BookMarked size={14}/>{student.course || 'Program not assigned'}</span></div>
        <div className="cf12-profile-details"><div><span>EMAIL</span><b><Mail size={15}/>{student.email || 'Not provided'}</b></div><div><span>AGE</span><b><UserRound size={15}/>{student.age || 'Not provided'}</b></div></div>
        <div className="cf12-profile-stats"><div><span>AVERAGE MARKS</span><b>{showPercent(score)}</b></div><div><span>ATTENDANCE</span><b>{showPercent(student.attendance_rate)}</b></div><div><span>SUBJECTS</span><b>{entries.length}</b></div></div>
        {canManage && <div className="cf12-profile-actions"><button onClick={onMarks}><Plus size={16}/> Add marks</button><button onClick={onAttendance}><CalendarDays size={16}/> Attendance</button></div>}
        <div className="cf12-profile-tabs" role="tablist"><button role="tab" aria-selected={tab==='marks'} className={tab==='marks'?'selected':''} onClick={()=>setTab('marks')}>Marks ({entries.length})</button><button role="tab" aria-selected={tab==='attendance'} className={tab==='attendance'?'selected':''} onClick={()=>setTab('attendance')}>Attendance ({present.length})</button></div>
        {tab==='marks' ? <div className="cf12-profile-list">{entries.length ? entries.map(m=><div key={m.id}><span><b>{m.subject}</b><small>{m.semester || 'Unassigned semester'}</small></span><strong>{Number(m.marks).toFixed(0)}/100</strong></div>) : <p className="cf12-profile-empty">No assessment results yet.</p>}</div> : <div className="cf12-profile-list">{present.length ? present.slice(0,30).map(r=><div key={r.id}><span><b>{r.date}</b><small>{r.semester || 'Unassigned semester'}</small></span><strong className={r.status==='P'?'cf12-present':'cf12-absent'}>{r.status==='P'?'Present':'Absent'}</strong></div>) : <p className="cf12-profile-empty">No attendance records yet.</p>}</div>}
      </div>
    </aside>
  </div>;
}

export function ActionInsights({ students, onNavigate }) {
  const needMarks = students.filter(s=>s.average == null).length;
  const needAttendance = students.filter(s=>s.attendance_rate == null).length;
  const lowAttendance = students.filter(s=>s.attendance_rate != null && Number(s.attendance_rate)<75).length;
  const items = [
    {name:'Missing assessment records', desc:`${needMarks} student${needMarks===1?'':'s'} without marks`, count:needMarks, icon:BookOpen, route:'grades', kind:'purple'},
    {name:'Attendance not recorded', desc:`${needAttendance} student${needAttendance===1?'':'s'} without attendance`, count:needAttendance, icon:CalendarDays, route:'attendance', kind:'blue'},
    {name:'Review low attendance', desc:`${lowAttendance} student${lowAttendance===1?'':'s'} below 75%`, count:lowAttendance, icon:AlertCircle, route:'students', kind:'orange'}
  ];
  return <section className="cf12-insights"><div className="cf12-insights-heading"><div><span className="cf12-overline">WORKSPACE INSIGHTS</span><h2>Where to focus next</h2><p>Actions based on your current records, not fictional data.</p></div><span className="cf12-insights-live"><span/> Live records</span></div><div className="cf12-insights-grid">{items.map(item=><button key={item.name} onClick={()=>onNavigate(item.route)} className="cf12-insight"><div className={`cf12-insight-icon ${item.kind}`}><item.icon size={20}/></div><div><strong>{item.name}</strong><p>{item.count ? item.desc : 'Everything up to date'}</p></div><span className="cf12-insight-chevron"><ArrowRight size={17}/></span></button>)}</div>{students.length===0&&<p className="cf12-insights-note">Add students to start receiving record quality suggestions.</p>}</section>;
}

export const defaultPreferences = {compactTables:false, reduceMotion:false, showWelcome:true};
export function loadPreferences() {
  try {const value=JSON.parse(window.localStorage.getItem('campusflow-display') || '{}');return {...defaultPreferences,...Object.fromEntries(Object.entries(value).filter(([key,val])=>key in defaultPreferences && typeof val==='boolean'))};}
  catch {return {...defaultPreferences};}
}
export function savePreferences(value) {try {window.localStorage.setItem('campusflow-display',JSON.stringify(value));}catch { /* blocked storage: apply current session only */ }}

export function PreferencesPage({ user, prefs, setPrefs }) {
  const toggles = [
    {key:'compactTables', label:'Compact table rows', description:'Show more students and academic records without scrolling.',icon:GraduationCap},
    {key:'reduceMotion', label:'Reduce motion', description:'Turn off optional animations and hover movement.',icon:CircleHelp},
    {key:'showWelcome', label:'Show dashboard welcome panel', description:'Keep the illustrated welcome panel visible on Overview.',icon:LayoutDashboard}
  ];
  return <div className="cf12-settings-page"><div className="page-heading inner-page-heading"><div><div className="eyebrow"><span className="eyebrow-dot"/> PERSONALIZE</div><h1>Workspace preferences</h1><p>Make CampusFlow comfortable and efficient for your day-to-day work.</p></div></div>
    <section className="cf12-settings-card"><div className="cf12-settings-card-head"><Settings size={21}/><div><h2>Display and accessibility</h2><p>Changes save automatically on this browser.</p></div></div>
      {toggles.map(item=><label className="cf12-settings-row" key={item.key}><span className="cf12-settings-icon"><item.icon size={20}/></span><span className="cf12-settings-copy"><strong>{item.label}</strong><small>{item.description}</small></span><input type="checkbox" checked={prefs[item.key]} onChange={e=>setPrefs(prev=>({...prev,[item.key]:e.target.checked}))}/><span className="cf12-toggle" aria-hidden="true"/></label>)}
    </section>
    <section className="cf12-settings-card"><div className="cf12-settings-card-head"><Keyboard size={21}/><div><h2>Keyboard shortcuts</h2><p>Navigate your workspace quickly.</p></div></div><div className="cf12-shortcut"><span>Search everything</span><span><kbd>Ctrl</kbd> + <kbd>K</kbd></span></div><div className="cf12-shortcut"><span>Close open dialogs</span><span><kbd>Esc</kbd></span></div></section>
    <section className="cf12-settings-card"><div className="cf12-settings-card-head"><ShieldCheck size={21}/><div><h2>Account</h2><p>Signed in with your existing CampusFlow credentials.</p></div></div><div className="cf12-account-meta"><span>Username <b>{user.username}</b></span><span>Access level <b>{user.role==='admin'?'Administrator':'Teacher'}</b></span></div><p className="cf12-settings-hint">These are display preferences only. Student records and account details are not changed.</p></section>
  </div>;
}
