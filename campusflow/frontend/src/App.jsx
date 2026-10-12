import React, { useCallback, useEffect, useMemo, useState } from 'react';
import {
  LayoutDashboard, GraduationCap, ClipboardCheck, BookOpen, ChartNoAxesCombined,
  Sparkles, Settings, PanelLeftClose, PanelLeftOpen, Menu, Bell, Search, ChevronDown,
  ChevronRight, Plus, ArrowUpRight, ArrowRight, Download, SlidersHorizontal,
  CalendarDays, UsersRound, Target, Clock3, TrendingUp, Ellipsis, X, Check,
  Pencil, Trash2, RefreshCcw, AlertCircle, BookMarked, MoreHorizontal, LogOut,
  CircleHelp, Command, Filter, FileBarChart, Lightbulb, ShieldCheck, CheckCircle2,
  ArrowDownToLine, MessageCircle, BadgeCheck, BrainCircuit, FileUp, CalendarRange, FileBadge2
} from 'lucide-react';
import {
  ResponsiveContainer, AreaChart, Area, CartesianGrid, XAxis, YAxis, Tooltip,
  PieChart, Pie, Cell, BarChart, Bar, Legend
} from 'recharts';
import { api, clearSession, hasSession } from './api';
import AuthScreen from './AuthScreen';
import AccountsPage from './AccountsPage';
import ReportsPage from './ReportsPage';
import AssistantPage from './AssistantPage';
import PredictionPage from './PredictionPage';
import ImportPage from './ImportPage';
import CalendarPage from './CalendarPage';
import BrandingPage from './BrandingPage';
import { CommandPalette, StudentProfile, ActionInsights, PreferencesPage, loadPreferences, savePreferences } from './Experience';

const NAV = [
  { key: 'overview', name: 'Overview', icon: LayoutDashboard },
  { key: 'students', name: 'Students', icon: GraduationCap },
  { key: 'attendance', name: 'Attendance', icon: ClipboardCheck },
  { key: 'grades', name: 'Grades & marks', icon: BookOpen },
  { key: 'reports', name: 'Reports', icon: ChartNoAxesCombined },
  { key: 'calendar', name: 'Academic calendar', icon: CalendarRange },
  { key: 'import', name: 'Import students', icon: FileUp, adminOnly: true },
  { key: 'branding', name: 'University branding', icon: FileBadge2, adminOnly: true },
  { key: 'assistant', name: 'AI Assistant', icon: Sparkles },
  { key: 'prediction', name: 'ML Predictions', icon: BrainCircuit, adminOnly: true },
];
const COLORS = ['#705cf2', '#3fc7b2', '#f5b95c', '#78a6fa', '#ed92a1', '#aa98ff', '#84c1d9', '#9cabba'];
const initials = name => (name || '?').split(/\s+/).slice(0, 2).map(s => s[0] || '').join('').toUpperCase();
const percent = n => n == null ? '—' : `${Number(n).toFixed(1).replace(/\.0$/, '')}%`;
const scoreText = n => n == null ? '—' : `${Number(n).toFixed(1).replace(/\.0$/, '')}%`;
const todayISO = () => { const d = new Date(); return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')}`; };
const emptyStudent = { id: '', name: '', age: '', email: '', course: '' };
const cx = (...args) => args.filter(Boolean).join(' ');

function ProfileAvatar({ name, index = 0, size = '' }) {
  return <span className={cx('avatar', size)} style={{ '--av-bg': ['#eee9ff', '#e4f5f5', '#fff2de', '#e8efff', '#ffeaf0'][index % 5], '--av-fg': ['#7059d9','#178f83','#ae7829','#4b70bd','#ca5d7c'][index % 5] }}>{initials(name)}</span>;
}

function ChartTooltip({ active, payload, label, suffix = '' }) {
  if (!active || !payload?.length) return null;
  return <div className="chart-tooltip"><strong>{label || payload[0]?.name}</strong>{payload.filter(p => p.value != null).map((p, i) => <div key={i} style={{ color: p.color || '#6654db' }}>{p.name}: {p.value}{suffix}</div>)}</div>;
}

function Sidebar({ page, setPage, collapsed, setCollapsed, mobileOpen, setMobileOpen, user }) {
  return <>
    {mobileOpen && <button aria-label="Close navigation" className="mobile-scrim" onClick={() => setMobileOpen(false)}/>}
    <aside className={cx('sidebar', collapsed && 'sidebar-collapsed', mobileOpen && 'sidebar-mobile-open')}>
      <div className="brand-box">
        <div className="brand-mark"><GraduationCap size={23} strokeWidth={2.6}/></div>
        {!collapsed && <div className="brand-name">campus<span>flow</span><small>ACADEMIC WORKSPACE</small></div>}
      </div>
      <div className="sidebar-scroll">
        {!collapsed && <p className="side-caption">PHASE 13 · SMART CAMPUS</p>}
        <nav aria-label="Main navigation" className="side-nav">
          {NAV.filter(item => !item.adminOnly || user.role === 'admin').map(({ key, name, icon: Icon }) => <button key={key} title={name} onClick={() => { setPage(key); setMobileOpen(false); }} className={cx('nav-item', page === key && 'nav-active')}>
            <Icon size={19}/>{!collapsed && <><span>{name}</span>{page === key && <span className="active-dot"/>}</>}
          </button>)}
        </nav>
        {user.role==='admin' && <button className={cx('nav-item',page==='accounts'&&'nav-active')} onClick={()=>{setPage('accounts');setMobileOpen(false);}} title="Team access"><ShieldCheck size={19}/>{!collapsed && <span>Team access</span>}</button>}
        {!collapsed && <p className="side-caption side-caption-second">SETTINGS</p>}
        <button className={cx('nav-item',page==='settings'&&'nav-active')} onClick={() => {setPage('settings');setMobileOpen(false);}} title="Preferences"><Settings size={19}/>{!collapsed && <span>Preferences</span>}</button>
      </div>
      <div className="sidebar-bottom">
        {!collapsed && <div className="sidebar-help"><div className="help-orb"><Sparkles size={19}/></div><strong>Level up your insights</strong><p>Your academic assistant is ready to explore.</p><button onClick={() => setPage('assistant')}>Ask the assistant <ArrowUpRight size={14}/></button></div>}
        <button className="collapse-btn" onClick={() => setCollapsed(!collapsed)} title={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}>{collapsed ? <PanelLeftOpen size={17}/> : <PanelLeftClose size={17}/>} {!collapsed && 'Collapse sidebar'}</button>
      </div>
    </aside>
  </>;
}

function Header({ page, setMobileOpen, refresh, busy, notify, user, onLogout, onSearch }) {
  const titles = { overview: 'Dashboard', students: 'Students', attendance: 'Attendance', grades: 'Grades & marks', reports: 'Reports', calendar: 'Academic calendar', import: 'Import students', branding: 'University branding', assistant: 'AI Assistant', prediction: 'ML Predictions', accounts: 'Team access', settings: 'Preferences' };
  return <header className="topbar">
    <div className="breadcrumb"><button className="mobile-menu icon-action" onClick={() => setMobileOpen(true)} aria-label="Open navigation"><Menu size={21}/></button><span className="crumb-muted">Workspace</span><ChevronRight size={15}/><span>{titles[page]}</span></div>
    <div className="top-actions">
      <button className="header-search" onClick={onSearch}><Search size={17}/><span>Search anything</span><kbd>Ctrl K</kbd></button>
      <button aria-label="Refresh data" title="Refresh data" className="icon-action" onClick={refresh}><RefreshCcw size={19} className={busy ? 'spinning' : ''}/></button>
      <button aria-label="Notifications" title="Notifications" className="icon-action notif-icon" onClick={() => notify('You’re all caught up!','success')}><Bell size={19}/><i/></button>
      <span className="top-separator"/>
      <div className="profile-chip" title={`Signed in as ${user.username}`}><span className="profile-initials">{initials(user.username)}</span><span className="profile-text"><b>{user.username}</b><small>{user.role==='admin'?'Administrator':'Teacher'}</small></span></div><button className="icon-action logout-icon" onClick={onLogout} aria-label="Sign out" title="Sign out"><LogOut size={19}/></button>
    </div>
  </header>;
}

function StatCard({ label, value, icon: Icon, note, tone, statIcon }) {
  return <div className="stat-card">
    <div className="stat-top"><span className={cx('stat-icon', `tone-${tone}`)}><Icon size={21}/></span><span className="stat-mini"><ArrowUpRight size={15}/></span></div>
    <div className="stat-label">{label}</div><div className="stat-value">{value}</div><div className="stat-foot"><span className="foot-dot"/> {note}</div>
  </div>;
}

function SectionHeading({ title, sub, action, onClick }) {
  return <div className="section-heading"><div><h3>{title}</h3>{sub && <p>{sub}</p>}</div>{action && <button className="text-link" onClick={onClick}>{action}<ArrowRight size={16}/></button>}</div>;
}

function EmptyChart({ message = 'Add student records to see the chart.' }) {
  return <div className="empty-chart"><span><ChartNoAxesCombined size={25}/></span><strong>Nothing to visualize yet</strong><p>{message}</p></div>;
}

function CoursesChart({ data }) {
  const chartData = data.slice(0, 6);
  return <div className="chart-panel chart-panel-large"><SectionHeading title="Students by course" sub="Enrollment distribution across programs"/><div className="chart-main">
    {chartData.length ? <ResponsiveContainer width="100%" height="100%" minHeight={230}>
      <BarChart data={chartData} layout="vertical" margin={{ top: 5, right: 22, left: 8, bottom: 4 }} barCategoryGap={15}>
        <CartesianGrid horizontal={false} stroke="#edf0f6" strokeDasharray="4 4"/>
        <XAxis type="number" allowDecimals={false} axisLine={false} tickLine={false} tick={{ fill:'#a2a9b9',fontSize:11 }}/>
        <YAxis type="category" dataKey="name" width={114} axisLine={false} tickLine={false} tick={{fill:'#687287',fontSize:11}} tickFormatter={name => name.length > 18 ? `${name.slice(0, 16)}…` : name}/>
        <Tooltip content={<ChartTooltip/>} cursor={{fill:'#f9f8ff'}}/>
        <Bar dataKey="value" name="Students" radius={[0,6,6,0]} maxBarSize={22}>
          {chartData.map((entry,i) => <Cell key={entry.name} fill={COLORS[i % COLORS.length]}/>)}
        </Bar>
      </BarChart>
    </ResponsiveContainer> : <EmptyChart/>}
  </div></div>;
}

function DonutChart({ data, total }) {
  const nonempty = data.filter(d => d.value > 0).slice(0, 5);
  return <div className="chart-panel"><SectionHeading title="Course breakdown" sub="Student distribution"/><div className="donut-body">
    {nonempty.length ? <><div className="donut-chart"><ResponsiveContainer width="100%" height="100%"><PieChart><Pie data={nonempty} dataKey="value" nameKey="name" innerRadius="70%" outerRadius="93%" paddingAngle={3} stroke="none" cornerRadius={4}>{nonempty.map((item,i) => <Cell key={item.name} fill={COLORS[i]}/>)}</Pie><Tooltip formatter={(value,name) => [`${value} students`,name]}/></PieChart></ResponsiveContainer><div className="donut-center"><strong>{total}</strong><span>Students</span></div></div><div className="legend-list">{nonempty.map((d,i) => <div className="legend-row" key={d.name}><span className="legend-dot" style={{backgroundColor:COLORS[i]}}/><span title={d.name}>{d.name}</span><b>{total ? Math.round(d.value*100/total) : 0}%</b></div>)}</div></> : <EmptyChart/>}
  </div></div>;
}

function AttendanceChart({ data }) {
  const valid = data.some(d => d.attendance !== null);
  return <div className="chart-panel"><SectionHeading title="Attendance trend" sub="Monthly presence rate · last 6 months"/><div className="chart-main">
    {valid ? <ResponsiveContainer width="100%" height="100%" minHeight={230}><AreaChart data={data} margin={{top:9,right:13,bottom:3,left:-18}}>
      <defs><linearGradient id="attGradient" x1="0" x2="0" y1="0" y2="1"><stop offset="0%" stopColor="#7665f3" stopOpacity={0.2}/><stop offset="100%" stopColor="#7665f3" stopOpacity={0}/></linearGradient></defs>
      <CartesianGrid stroke="#f0f1f6" vertical={false} strokeDasharray="4 4"/>
      <XAxis dataKey="month" axisLine={false} tickLine={false} tick={{fill:'#929bab',fontSize:11}} dy={10}/>
      <YAxis domain={[0,100]} axisLine={false} tickLine={false} tick={{fill:'#929bab',fontSize:11}} tickFormatter={v=>`${v}%`}/>
      <Tooltip content={<ChartTooltip suffix="%"/>}/>
      <Area type="monotone" name="Attendance" dataKey="attendance" stroke="#7665f3" strokeWidth={3} fill="url(#attGradient)" connectNulls dot={{r:3,strokeWidth:2,fill:'#fff'}} activeDot={{r:5}}/>
    </AreaChart></ResponsiveContainer> : <EmptyChart message="Record attendance to view monthly trends."/>}
  </div></div>;
}

function SubjectChart({ data }) {
  return <div className="chart-panel"><SectionHeading title="Subject performance" sub="Average scores by subject"/><div className="chart-main">
    {data.length ? <ResponsiveContainer width="100%" height="100%" minHeight={230}><BarChart data={data.slice(0, 6)} margin={{top:10,right:12,bottom:15,left:-18}}>
      <CartesianGrid stroke="#edf0f6" vertical={false} strokeDasharray="4 4"/>
      <XAxis dataKey="name" axisLine={false} tickLine={false} tick={{fill:'#8a94a7',fontSize:10}} interval={0} angle={-18} textAnchor="end" height={52} tickFormatter={name => name.length>13 ? `${name.slice(0,11)}…`: name}/>
      <YAxis domain={[0,100]} axisLine={false} tickLine={false} tick={{fill:'#9da6b6',fontSize:11}}/>
      <Tooltip content={<ChartTooltip suffix="%"/>}/>
      <Bar name="Average score" dataKey="score" fill="#6f5dea" radius={[6,6,0,0]} maxBarSize={32}/>
    </BarChart></ResponsiveContainer> : <EmptyChart message="Add subject marks to see performance."/>}
  </div></div>;
}

function WelcomeBanner({ onCreate }) {
  return <div className="welcome-banner">
    <div className="welcome-copy"><span className="welcome-eyebrow"><Sparkles size={13}/> YOUR ACADEMIC WORKSPACE</span><h2>Make every student<br/><em>success story count.</em></h2><p>All your student insights, performance, and records in one beautiful place.</p>{onCreate && <button onClick={onCreate}>Add new student <ArrowRight size={17}/></button>}</div>
    <div className="banner-art" aria-hidden="true"><div className="art-circle circle-one"/><div className="art-circle circle-two"/><div className="art-paper"><span className="paper-top"><span/><span/></span><span className="paper-line long"/><span className="paper-line medium"/><span className="paper-bars"><i/><i/><i/><i/><i/><i/></span><span className="paper-line short"/></div><div className="art-badge"><TrendingUp size={22}/></div><div className="art-star star-one">✦</div><div className="art-star star-two">✧</div></div>
  </div>;
}

function StudentTable({ students, onViewAll, onView, limit = 5, compact = false }) {
  const items = limit ? students.slice(0,limit) : students;
  return <div className="table-wrap"><table className="data-table"><thead><tr><th>STUDENT</th><th>STUDENT ID</th><th>PROGRAM</th><th>AVG. SCORE</th><th>ATTENDANCE</th>{!compact && <th aria-label="Actions"/>}</tr></thead><tbody>
    {items.map((s,i) => <tr key={s.id}><td><div className="student-person"><ProfileAvatar name={s.name} index={i}/><span><button className="cf12-student-link" onClick={() => onView?.(s)}>{s.name}</button><small>{s.email || 'No email available'}</small></span></div></td><td><span className="mono muted">#{s.id}</span></td><td><span className="table-course">{s.course}</span></td><td><div className="score-col"><span>{scoreText(s.average)}</span><span className="score-track"><i style={{width:`${Math.min(100,Math.max(0,s.average||0))}%`}}/></span></div></td><td><span className={cx('status-pill', s.attendance_rate == null ? 'status-neutral' : s.attendance_rate >= 80 ? 'status-good':'status-warn')}>{percent(s.attendance_rate)}</span></td>{!compact && <td><button onClick={() => onView(s)} className="row-action" title={`View ${s.name}`} aria-label={`View ${s.name}`}><ArrowUpRight size={16}/></button></td>}</tr>)}
    {!items.length && <tr><td colSpan={compact ? 5 : 6} className="empty-row">No students found. Add your first student to get started.</td></tr>}
  </tbody></table>{onViewAll && <button className="table-footer-link" onClick={onViewAll}>View all students <ArrowRight size={16}/></button>}</div>;
}

function Overview({ data, students, setPage, openStudentModal, onView, user, showWelcome }) {
  const stats = data?.stats || {};
  return <>
    <div className="page-heading"><div><div className="eyebrow"><span className="eyebrow-dot"/> OVERVIEW</div><h1>Good to see you, {user.username} <span className="wave">✳</span></h1><p>Here's what's happening across your academic workspace.</p></div><div className="heading-actions"><span className="date-chip"><CalendarDays size={16}/>{new Date().toLocaleDateString('en-US',{month:'short',day:'numeric',year:'numeric'})}</span>{openStudentModal && <button className="primary-btn" onClick={() => openStudentModal()}><Plus size={18}/> Add student</button>}</div></div>
    {showWelcome && <WelcomeBanner onCreate={openStudentModal}/> }
    <section className="cf13-launch" aria-label="Phase 13 features">
      <div className="cf13-launch-heading"><span className="cf13-launch-tag">NEW · PHASE 13</span><div><h2>Smart campus toolkit</h2><p>New tools are now available in your workspace.</p></div></div>
      <div className="cf13-launch-links">
        <button onClick={()=>setPage('calendar')}><CalendarRange size={21}/><span><b>Academic calendar</b><small>Exams, events and deadlines</small></span><ArrowUpRight size={16}/></button>
        {user.role==='admin' && <button onClick={()=>setPage('import')}><FileUp size={21}/><span><b>Import students</b><small>Upload Excel or CSV records</small></span><ArrowUpRight size={16}/></button>}
        {user.role==='admin' && <button onClick={()=>setPage('branding')}><FileBadge2 size={21}/><span><b>University branding</b><small>Professional PDF reports</small></span><ArrowUpRight size={16}/></button>}
        <button onClick={()=>setPage('assistant')}><Sparkles size={21}/><span><b>Live data assistant</b><small>No Ollama or API key needed</small></span><ArrowUpRight size={16}/></button>
      </div>
    </section>
    <div className="stat-grid"><StatCard label="Total students" value={stats.students ?? 0} icon={UsersRound} note="Students in your database" tone="purple"/><StatCard label="Active programs" value={stats.courses ?? 0} icon={BookMarked} note="Unique enrolled courses" tone="blue"/><StatCard label="Average score" value={percent(stats.average)} icon={Target} note="Based on recorded marks" tone="mint"/><StatCard label="Attendance rate" value={percent(stats.attendance)} icon={ClipboardCheck} note="Across recorded sessions" tone="amber"/></div>
    <ActionInsights students={students} onNavigate={setPage}/>
    <div className="dashboard-grid"><CoursesChart data={data?.courses || []}/><DonutChart data={data?.courses || []} total={stats.students || 0}/><AttendanceChart data={data?.attendance_trend || []}/><SubjectChart data={data?.subjects || []}/></div>
    <div className="recent-panel"><SectionHeading title="Recently added students" sub="Your latest student records" action="View all students" onClick={() => setPage('students')}/><StudentTable compact students={students} limit={5} onView={onView}/></div>
  </>;
}

function ToolbarTitle({ tag, title, description, buttonText, onButton, icon: Icon = Plus }) {
  return <div className="page-heading inner-page-heading"><div><div className="eyebrow"><span className="eyebrow-dot"/> {tag}</div><h1>{title}</h1><p>{description}</p></div>{buttonText && <button className="primary-btn" onClick={onButton}><Icon size={17}/>{buttonText}</button>}</div>;
}

function StudentsPage({ students, onAdd, onEdit, onDelete, onView, canManage }) {
  const [query,setQuery] = useState('');
  const [course,setCourse] = useState('All programs');
  const filtered = useMemo(() => students.filter(s => (`${s.name} ${s.id} ${s.email} ${s.course}`).toLowerCase().includes(query.toLowerCase()) && (course==='All programs' || s.course===course)),[students,query,course]);
  const courses = Array.from(new Set(students.map(s=>s.course).filter(Boolean))).sort();
  return <><ToolbarTitle tag="STUDENT DIRECTORY" title="Student management" description="Organize your students and keep every record up to date." buttonText={canManage?"Add student":null} onButton={()=>onAdd()}/><div className="page-info-grid"><div className="mini-stat"><UsersRound size={20}/><span><strong>{students.length}</strong><small>Total students</small></span></div><div className="mini-stat"><BookMarked size={20}/><span><strong>{courses.length}</strong><small>Programs</small></span></div><div className="mini-stat"><CheckCircle2 size={20}/><span><strong>{students.filter(s=>s.average!=null).length}</strong><small>With marks</small></span></div></div><div className="table-panel"><div className="table-panel-head"><div><h3>Student directory</h3><p>{filtered.length} records found</p></div><div className="filters"><div className="search-field"><Search size={18}/><input aria-label="Search students" placeholder="Search name, ID, course..." value={query} onChange={e=>setQuery(e.target.value)}/>{query && <button onClick={()=>setQuery('')} aria-label="Clear search"><X size={15}/></button>}</div><select aria-label="Filter by program" value={course} onChange={e=>setCourse(e.target.value)}><option>All programs</option>{courses.map(c=><option key={c}>{c}</option>)}</select></div></div><div className="table-wrap"><table className="data-table"><thead><tr><th>STUDENT</th><th>ID</th><th>PROGRAM</th><th>AVG. SCORE</th><th>ATTENDANCE</th><th>ACTIONS</th></tr></thead><tbody>{filtered.map((s,i)=><tr key={s.id}><td><div className="student-person"><ProfileAvatar name={s.name} index={i}/><span><button className="cf12-student-link" onClick={()=>onView(s)}>{s.name}</button><small>{s.email||'No email provided'}</small></span></div></td><td className="mono muted">#{s.id}</td><td>{s.course}</td><td><div className="score-col"><span>{percent(s.average)}</span><span className="score-track"><i style={{width:`${s.average||0}%`}}/></span></div></td><td><span className={cx('status-pill',s.attendance_rate == null?'status-neutral':s.attendance_rate>=80?'status-good':'status-warn')}>{percent(s.attendance_rate)}</span></td><td><div className="table-actions"><button aria-label={`View ${s.name}`} title="Student profile" onClick={()=>onView(s)}><ArrowUpRight size={16}/></button>{canManage&&<><button aria-label={`Edit ${s.name}`} title="Edit student" onClick={()=>onEdit(s)}><Pencil size={16}/></button><button className="danger-icon" aria-label={`Delete ${s.name}`} title="Delete student" onClick={()=>onDelete(s)}><Trash2 size={16}/></button></>}</div></td></tr>)}{!filtered.length && <tr><td colSpan={6} className="empty-row">No students match your filters.</td></tr>}</tbody></table></div></div></>;
}

function AttendancePage({ attendance, students, onAdd }) {
  const [query,setQuery] = useState('');
  const [status,setStatus] = useState('all');
  const filtered = attendance.filter(r=>(`${r.student_name} ${r.student_id} ${r.course} ${r.date}`).toLowerCase().includes(query.toLowerCase()) && (status==='all'||r.status===status));
  const present = attendance.filter(r=>r.status==='P').length;
  return <><ToolbarTitle tag="DAILY ATTENDANCE" title="Attendance tracking" description="Keep daily records accurate and easy to review." buttonText="Record attendance" onButton={onAdd}/><div className="page-info-grid"><div className="mini-stat"><ClipboardCheck size={20}/><span><strong>{attendance.length}</strong><small>Total records</small></span></div><div className="mini-stat"><CheckCircle2 size={20}/><span><strong>{present}</strong><small>Present entries</small></span></div><div className="mini-stat"><Target size={20}/><span><strong>{attendance.length?percent(100*present/attendance.length):'—'}</strong><small>Presence rate</small></span></div></div><div className="table-panel"><div className="table-panel-head"><div><h3>Attendance register</h3><p>Records are ordered by date</p></div><div className="filters"><div className="search-field"><Search size={18}/><input placeholder="Search records..." aria-label="Search attendance" value={query} onChange={e=>setQuery(e.target.value)}/></div><select aria-label="Filter attendance" value={status} onChange={e=>setStatus(e.target.value)}><option value="all">All statuses</option><option value="P">Present</option><option value="A">Absent</option></select></div></div><div className="table-wrap"><table className="data-table"><thead><tr><th>STUDENT</th><th>STUDENT ID</th><th>PROGRAM</th><th>DATE</th><th>SEMESTER</th><th>STATUS</th></tr></thead><tbody>{filtered.slice(0,250).map((r,i)=><tr key={r.id}><td><div className="student-person"><ProfileAvatar name={r.student_name} index={i}/><strong>{r.student_name}</strong></div></td><td className="mono muted">#{r.student_id}</td><td>{r.course}</td><td>{r.date}</td><td>{r.semester || 'Unassigned'}</td><td><span className={cx('status-pill',r.status==='P'?'status-good':'status-warn')}>{r.status==='P'?'Present':'Absent'}</span></td></tr>)}{!filtered.length && <tr><td colSpan="6" className="empty-row">No attendance records found.</td></tr>}</tbody></table></div>{filtered.length>250 && <p className="table-caption">Showing 250 newest matching records.</p>}</div></>;
}

function GradesPage({ marks, onAdd }) {
  const [query,setQuery] = useState('');
  const filtered = marks.filter(m=>(`${m.student_name} ${m.student_id} ${m.subject}`).toLowerCase().includes(query.toLowerCase()));
  const average = marks.length ? marks.reduce((a,m)=>a+Number(m.marks),0)/marks.length : null;
  return <><ToolbarTitle tag="ACADEMIC RESULTS" title="Grades & marks" description="See how students perform across their subjects." buttonText="Add marks" onButton={onAdd}/><div className="page-info-grid"><div className="mini-stat"><BookOpen size={20}/><span><strong>{marks.length}</strong><small>Assessments recorded</small></span></div><div className="mini-stat"><Target size={20}/><span><strong>{percent(average)}</strong><small>Average score</small></span></div><div className="mini-stat"><BookMarked size={20}/><span><strong>{new Set(marks.map(m=>m.subject.toLowerCase())).size}</strong><small>Subjects</small></span></div></div><div className="table-panel"><div className="table-panel-head"><div><h3>Assessment records</h3><p>Adding marks again for a subject updates its existing result</p></div><div className="search-field"><Search size={18}/><input placeholder="Search student or subject..." aria-label="Search marks" value={query} onChange={e=>setQuery(e.target.value)}/></div></div><div className="table-wrap"><table className="data-table"><thead><tr><th>STUDENT</th><th>ID</th><th>SUBJECT</th><th>SEMESTER</th><th>MARKS</th><th>GRADE</th></tr></thead><tbody>{filtered.map((m,i)=>{const v=Number(m.marks);const grade=v>=90?'A+':v>=80?'A':v>=70?'B':v>=60?'C':v>=50?'D':'F';return <tr key={m.id}><td><div className="student-person"><ProfileAvatar name={m.student_name} index={i}/><strong>{m.student_name}</strong></div></td><td className="mono muted">#{m.student_id}</td><td>{m.subject}</td><td><span className="table-course">{m.semester || 'Unassigned'}</span></td><td><div className="score-col"><span>{v}/100</span><span className="score-track"><i style={{width:`${Math.min(100,Math.max(0,v))}%`}}/></span></div></td><td><span className={cx('grade-badge',grade==='F'?'grade-low':grade==='A+'||grade==='A'?'grade-high':'grade-mid')}>{grade}</span></td></tr>})}{!filtered.length&&<tr><td colSpan="6" className="empty-row">No marks have been recorded yet.</td></tr>}</tbody></table></div></div></>;
}


function Modal({ title, subtitle, children, onClose }) {
  return <div className="modal-shade" role="presentation" onMouseDown={e=>{if(e.target===e.currentTarget)onClose();}}><div className="modal" role="dialog" aria-modal="true" aria-label={title}><div className="modal-head"><div><h2>{title}</h2>{subtitle&&<p>{subtitle}</p>}</div><button className="icon-action" onClick={onClose} aria-label="Close"><X size={20}/></button></div><div className="modal-body">{children}</div></div></div>;
}

function StudentForm({ value, onSave, onClose, saving }) {
  const [form,setForm] = useState(value ? { ...value } : {...emptyStudent});
  const edit = Boolean(value);
  const set = (key,val) => setForm(old => ({...old,[key]:val}));
  function submit(e) { e.preventDefault();onSave({id:Number(form.id),name:form.name.trim(),age:Number(form.age),email:form.email.trim(),course:form.course.trim()},edit?value.id:null); }
  return <form onSubmit={submit} className="edit-form"><div className="form-grid"><label>Student ID <input type="number" min="1" required disabled={edit} value={form.id} onChange={e=>set('id',e.target.value)} placeholder="e.g. 1001"/></label><label>Age <input type="number" min="1" max="120" required value={form.age} onChange={e=>set('age',e.target.value)} placeholder="e.g. 20"/></label></div><label>Full name <input required maxLength="120" value={form.name} onChange={e=>set('name',e.target.value)} placeholder="Enter student name"/></label><label>Email address <input type="email" maxLength="200" value={form.email} onChange={e=>set('email',e.target.value)} placeholder="student@example.com"/></label><label>Program / course <input required maxLength="120" value={form.course} onChange={e=>set('course',e.target.value)} placeholder="e.g. Computer Science"/></label><div className="form-actions"><button type="button" className="outline-btn" onClick={onClose}>Cancel</button><button type="submit" disabled={saving} className="primary-btn">{saving?'Saving...': edit?'Save changes':'Add student'}</button></div></form>;
}

function MarksForm({ students, onSave, onClose, saving, initialStudentId }) {
  const [studentId,setStudentId] = useState(initialStudentId ? String(initialStudentId) : '');const [subject,setSubject] = useState('');const [marks,setMarks] = useState('');const [semester,setSemester] = useState('Semester 1');
  return <form onSubmit={e=>{e.preventDefault();onSave({student_id:Number(studentId),subject:subject.trim(),marks:Number(marks),semester});}} className="edit-form"><label>Student <select required value={studentId} onChange={e=>setStudentId(e.target.value)}><option value="">Choose student</option>{students.map(s=><option value={s.id} key={s.id}>{s.name} (#{s.id})</option>)}</select></label><label>Semester <select value={semester} onChange={e=>setSemester(e.target.value)}><option value="Unassigned">Unassigned</option>{Array.from({length:8},(_,i)=><option key={i} value={`Semester ${i+1}`}>Semester {i+1}</option>)}</select></label><label>Subject <input required maxLength="120" value={subject} onChange={e=>setSubject(e.target.value)} placeholder="e.g. Python Programming"/></label><label>Marks out of 100 <input required type="number" min="0" max="100" step="0.1" value={marks} onChange={e=>setMarks(e.target.value)} placeholder="e.g. 88"/></label><div className="form-actions"><button type="button" className="outline-btn" onClick={onClose}>Cancel</button><button type="submit" disabled={saving} className="primary-btn">{saving?'Saving...':'Save marks'}</button></div></form>;
}

function AttendanceForm({ students, onSave, onClose, saving, initialStudentId }) {
  const [studentId,setStudentId] = useState(initialStudentId ? String(initialStudentId) : '');const [day,setDay] = useState(todayISO());const [status,setStatus] = useState('P');const [semester,setSemester] = useState('Semester 1');
  return <form onSubmit={e=>{e.preventDefault();onSave({student_id:Number(studentId),date:day,status,semester});}} className="edit-form"><label>Student <select required value={studentId} onChange={e=>setStudentId(e.target.value)}><option value="">Choose student</option>{students.map(s=><option value={s.id} key={s.id}>{s.name} (#{s.id})</option>)}</select></label><label>Semester <select value={semester} onChange={e=>setSemester(e.target.value)}><option value="Unassigned">Unassigned</option>{Array.from({length:8},(_,i)=><option key={i} value={`Semester ${i+1}`}>Semester {i+1}</option>)}</select></label><label>Date <input required type="date" value={day} onChange={e=>setDay(e.target.value)}/></label><label>Attendance status <select value={status} onChange={e=>setStatus(e.target.value)}><option value="P">Present</option><option value="A">Absent</option></select></label><div className="form-actions"><button type="button" className="outline-btn" onClick={onClose}>Cancel</button><button type="submit" disabled={saving} className="primary-btn">{saving?'Saving...':'Save attendance'}</button></div></form>;
}

function Workspace({ user, onLogout }) {
  const canManage = user.role === 'admin';
  const [page,setPage] = useState('overview');
  const [collapsed,setCollapsed] = useState(false);
  const [mobileOpen,setMobileOpen] = useState(false);
  const [dashboard,setDashboard] = useState(null);
  const [students,setStudents] = useState([]);
  const [attendance,setAttendance] = useState([]);
  const [marks,setMarks] = useState([]);
  const [loading,setLoading] = useState(true);
  const [error,setError] = useState('');
  const [modal,setModal] = useState(null);
  const [saving,setSaving] = useState(false);
  const [toast,setToast] = useState(null);
  const [searchOpen,setSearchOpen] = useState(false);
  const [profile,setProfile] = useState(null);
  const [prefs,setPrefs] = useState(loadPreferences);

  const notify = useCallback((message, type = 'success') => setToast({message,type,id:Date.now()}),[]);
  useEffect(() => { if(!toast)return;const timer=setTimeout(()=>setToast(null),4200);return ()=>clearTimeout(timer);},[toast]);
  const refresh = useCallback(async () => {
    setLoading(true);
    try {
      const [d,s,a,m] = await Promise.all([api.dashboard(),api.students(),api.attendance(),api.marks()]);
      setDashboard(d);setStudents(s);setAttendance(a);setMarks(m);setError('');
    } catch(e) { setError(e.message || 'Could not load your data'); }
    finally { setLoading(false); }
  },[]);
  useEffect(()=>{refresh();},[refresh]);
  useEffect(()=>{savePreferences(prefs);},[prefs]);
  useEffect(()=>{const handle = e => {const el=e.target;const typing=el && (['INPUT','TEXTAREA','SELECT'].includes(el.tagName)||el.isContentEditable); if ((e.ctrlKey||e.metaKey) && e.key.toLowerCase()==='k'){e.preventDefault();setSearchOpen(open=>!open);}else if(e.key==='/'&&!typing&&!searchOpen&&!profile){e.preventDefault();setSearchOpen(true);}};window.addEventListener('keydown',handle);return ()=>window.removeEventListener('keydown',handle);},[searchOpen,profile]);

  async function saveStudent(payload, editId) {
    setSaving(true);
    try {if(editId!=null)await api.updateStudent(editId,payload);else await api.createStudent(payload);setModal(null);notify(editId!=null?'Student updated successfully':'Student added successfully');await refresh();}
    catch(e){notify(e.message,'error');} finally{setSaving(false);}
  }
  async function deleteStudent(student) {
    if(!window.confirm(`Delete ${student.name} and their marks/attendance records? This cannot be undone.`))return;
    try {await api.deleteStudent(student.id);notify('Student deleted');await refresh();}catch(e){notify(e.message,'error');}
  }
  async function saveMarks(payload){setSaving(true);try{await api.saveMarks(payload);setModal(null);notify('Marks saved successfully');await refresh();}catch(e){notify(e.message,'error');}finally{setSaving(false);}}
  async function saveAttendance(payload){setSaving(true);try{await api.saveAttendance(payload);setModal(null);notify('Attendance saved successfully');await refresh();}catch(e){notify(e.message,'error');}finally{setSaving(false);}}

  const downloadCSV = async () => {
    try {const blob=await api.exportStudents();const url=URL.createObjectURL(blob);const a=document.createElement('a');a.href=url;a.download='student-report.csv';document.body.appendChild(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),1000);notify('CSV export created');}catch(e){notify(e.message,'error');}
  };
  return <div className={cx('app-shell','cf12-refresh',collapsed&&'is-collapsed',prefs.compactTables&&'cf12-compact',prefs.reduceMotion&&'cf12-no-motion')}>
    <Sidebar page={page} setPage={setPage} collapsed={collapsed} setCollapsed={setCollapsed} mobileOpen={mobileOpen} setMobileOpen={setMobileOpen} user={user}/>
    <div className="app-right"><Header page={page} setMobileOpen={setMobileOpen} refresh={refresh} busy={loading} notify={notify} user={user} onLogout={onLogout} onSearch={()=>setSearchOpen(true)}/>
      <main className="content" id="main-content">
        {error && <div className="error-banner" role="alert"><AlertCircle size={20}/><div><b>Connection problem</b><p>{error}</p></div><button onClick={refresh}>Try again</button></div>}
        {!dashboard && loading ? <div className="loading-view"><span className="loader"/>Loading your workspace...</div> : <>
          {page === 'overview' && <Overview data={dashboard} students={students} setPage={setPage} openStudentModal={canManage ? () => setModal({kind:'student'}) : null} onView={setProfile} user={user} showWelcome={prefs.showWelcome}/>}
          {page === 'students' && <StudentsPage students={students} onAdd={()=>setModal({kind:'student'})} onEdit={s=>setModal({kind:'student',value:s})} onDelete={deleteStudent} onView={setProfile} canManage={canManage}/>}
          {page === 'attendance' && <AttendancePage attendance={attendance} students={students} onAdd={()=>setModal({kind:'attendance'})}/>}
          {page === 'grades' && <GradesPage marks={marks} onAdd={()=>setModal({kind:'marks'})}/>}
          {page === 'accounts' && canManage && <AccountsPage/>}
          {page === 'reports' && <ReportsPage user={user} students={students} refreshKey={dashboard} notify={notify} onDownloadStudents={downloadCSV}/>}
          {page === 'assistant' && <AssistantPage user={user}/>}
          {page === 'calendar' && <CalendarPage user={user}/>}
          {page === 'import' && canManage && <ImportPage onImported={refresh}/>}
          {page === 'branding' && canManage && <BrandingPage/>}
          {page === 'prediction' && canManage && <PredictionPage students={students}/>}
          {page === 'settings' && <PreferencesPage user={user} prefs={prefs} setPrefs={setPrefs}/>}
        </>}
        <footer className="page-footer"><span>© {new Date().getFullYear()} CampusFlow • Built with React & FastAPI</span><span><span className="online-dot"/> Protected academic workspace</span></footer>
      </main>
    </div>
    {searchOpen && <CommandPalette students={students} isAdmin={canManage} onClose={()=>setSearchOpen(false)} onPage={setPage} onStudent={setProfile}/>}
    {profile && <StudentProfile student={students.find(s=>s.id===profile.id)||profile} marks={marks} attendance={attendance} onClose={()=>setProfile(null)} canManage={canManage} onMarks={()=>{setModal({kind:'marks',studentId:profile.id});setProfile(null);}} onAttendance={()=>{setModal({kind:'attendance',studentId:profile.id});setProfile(null);}}/>}
    {toast&&<div className={cx('toast',toast.type==='error'&&'toast-error')} role="status">{toast.type==='error'?<AlertCircle size={19}/>:<CheckCircle2 size={19}/>}<span>{toast.message}</span><button aria-label="Dismiss notification" onClick={()=>setToast(null)}><X size={16}/></button></div>}
    {canManage && modal?.kind==='student' && <Modal title={modal.value?'Edit student':'Add new student'} subtitle="Keep your student directory up to date." onClose={()=>setModal(null)}><StudentForm value={modal.value} onSave={saveStudent} onClose={()=>setModal(null)} saving={saving}/></Modal>}
    {modal?.kind==='marks' && <Modal title="Record student marks" subtitle="Add or update a subject result." onClose={()=>setModal(null)}><MarksForm students={students} initialStudentId={modal.studentId} onSave={saveMarks} onClose={()=>setModal(null)} saving={saving}/></Modal>}
    {modal?.kind==='attendance' && <Modal title="Record attendance" subtitle="Save a present or absent entry for one day." onClose={()=>setModal(null)}><AttendanceForm students={students} initialStudentId={modal.studentId} onSave={saveAttendance} onClose={()=>setModal(null)} saving={saving}/></Modal>}
    {modal?.kind==='future' && <Modal title="Coming in the next phases" subtitle="We’re building the core experience first." onClose={()=>setModal(null)}><div className="roadmap-modal"><div><ShieldCheck size={22}/><span><b>Phase 8 — Secure accounts</b><small>Admin and teacher roles are now active.</small></span></div><div><Sparkles size={22}/><span><b>Phase 10 — Academic assistant</b><small>Now available in the sidebar</small></span></div><div><ChartNoAxesCombined size={22}/><span><b>Phase 11 — ML predictions</b><small>Local model with clearly marked demo mode and historical-outcome training</small></span></div><button className="primary-btn" onClick={()=>setModal(null)}>Got it</button></div></Modal>}
  </div>;
}

function App() {
  const [user,setUser] = useState(null);
  const [checking,setChecking] = useState(true);
  useEffect(() => {
    let active=true;
    if (hasSession()) api.me().then(u => {if(active)setUser(u);}).catch(() => clearSession()).finally(() => {if(active)setChecking(false);});
    else setChecking(false);
    const expired=()=>setUser(null);
    window.addEventListener('campusflow-session-expired',expired);
    return ()=>{active=false;window.removeEventListener('campusflow-session-expired',expired);};
  },[]);
  async function signOut() {
    try {await api.logout();} catch {clearSession();}
    setUser(null);
  }
  if (checking) return <div className="auth-checking"><span className="loader"/> Checking your session...</div>;
  if (!user) return <AuthScreen onSuccess={setUser}/>;
  return <Workspace user={user} onLogout={signOut}/>;
}

export default App;
