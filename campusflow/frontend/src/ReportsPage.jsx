import React, { useEffect, useMemo, useState } from 'react';
import {
  AlertCircle, ArrowDownToLine, BookOpen, CalendarDays, CheckCircle2, ClipboardCheck,
  Download, FileBarChart, FileText, GraduationCap, Layers3, RefreshCw, Target,
  TrendingUp, UsersRound
} from 'lucide-react';
import {
  ResponsiveContainer, AreaChart, Area, CartesianGrid, XAxis, YAxis, Tooltip,
  BarChart, Bar, Cell
} from 'recharts';
import { api } from './api';

const PALETTE = ['#7665e9','#4fc8b2','#eeb45c','#79a7f8','#ec91ae','#a997f5'];
const percent = value => value == null ? '—' : `${Number(value).toFixed(1).replace(/\.0$/, '')}%`;
const number = value => Number(value || 0).toLocaleString();
const SEMESTER_OPTIONS = ['Unassigned', ...Array.from({ length: 8 }, (_, i) => `Semester ${i + 1}`)];

function ReportStat({ icon: Icon, label, value, sub, tone = 'purple' }) {
  return <div className="p9-stat"><div className="p9-stat-head"><span className={`p9-icon p9-${tone}`}><Icon size={20}/></span><span className="p9-stat-caption">ACADEMIC REPORTS</span></div><div className="p9-stat-label">{label}</div><div className="p9-stat-number">{value}</div><div className="p9-stat-sub">{sub}</div></div>;
}
function Panel({ icon: Icon, title, description, children, wide=false }) {
  return <section className={`p9-panel ${wide ? 'p9-wide' : ''}`}><header className="p9-panel-head"><div className="p9-panel-icon"><Icon size={18}/></div><div><h3>{title}</h3><p>{description}</p></div></header>{children}</section>;
}
function Empty({ message }) {return <div className="p9-empty"><FileBarChart size={28}/><strong>No records for these filters</strong><p>{message || 'Add some results or choose different filters.'}</p></div>;}

export default function ReportsPage({ user, students, refreshKey, notify, onDownloadStudents }) {
  const [course, setCourse] = useState('');
  const [semester, setSemester] = useState('');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [exporting, setExporting] = useState('');
  const [studentId, setStudentId] = useState('');
  const canExport = user.role === 'admin';
  const badDates = Boolean(startDate && endDate && startDate > endDate);
  const filters = useMemo(() => ({ course, semester, start_date: startDate, end_date: endDate }), [course, semester, startDate, endDate]);

  useEffect(() => {
    if (badDates) { setError('The attendance start date must not be after the end date.'); setLoading(false); return; }
    let active = true;
    setLoading(true);
    setError('');
    api.reportAnalytics(filters)
      .then(data => {if (active) setReport(data);})
      .catch(err => {if(active) setError(err.message || 'Could not load reports');})
      .finally(() => {if(active)setLoading(false);});
    return () => {active=false;};
  }, [filters, refreshKey, badDates]);

  async function download(kind) {
    if (!canExport || badDates) return;
    if (kind === 'student' && !studentId) {notify('Choose a student to export.','error'); return;}
    setExporting(kind);
    try {
      const {blob,filename} = await api.downloadReport(kind, filters, studentId);
      const url = URL.createObjectURL(blob);
      const anchor = document.createElement('a');
      anchor.href=url; anchor.download=filename;
      document.body.appendChild(anchor); anchor.click();anchor.remove();
      setTimeout(()=>URL.revokeObjectURL(url),1000);
      notify('Report downloaded successfully');
    } catch (err) {notify(err.message || 'Download failed', 'error');}
    finally {setExporting('');}
  }

  const stats = report?.stats || {};
  const grades = report?.grades || [];
  const gradeCount = grades.reduce((sum, g)=>sum+g.count,0);
  const months = report?.attendance_monthly || [];
  const subjects = (report?.subjects || []).slice(0,8);
  const courses = report?.courses || [];
  const semesterOptions = Array.from(new Set([...SEMESTER_OPTIONS,...(report?.semesters || [])]));
  const trend = (report?.semester_trend || []).filter(x => x.average !== null);

  return <div className="p9-page">
    <div className="p9-titlebar"><div><div className="eyebrow"><span className="eyebrow-dot"/> PHASE 9 / INTELLIGENCE</div><h1>Academic reporting</h1><p>Turn student records into clear, actionable academic insights.</p></div><div className="p9-title-actions"><span className="p9-live-tag"><CheckCircle2 size={15}/> Live SQLite data</span></div></div>

    <section className="p9-filter-panel"><div className="p9-filter-title"><div><span className="p9-section-overline">REPORT CONFIGURATION</span><h2>Customize your report</h2><p>Choose a program, semester, and optional attendance dates.</p></div><button type="button" className="p9-reset" onClick={()=>{setCourse('');setSemester('');setStartDate('');setEndDate('');}}><RefreshCw size={15}/> Reset filters</button></div><div className="p9-filter-grid"><label>Program<select value={course} onChange={e=>setCourse(e.target.value)}><option value="">All programs</option>{courses.map(x=><option key={x} value={x}>{x}</option>)}</select></label><label>Semester<select value={semester} onChange={e=>setSemester(e.target.value)}><option value="">All semesters</option>{semesterOptions.map(x=><option key={x} value={x}>{x}</option>)}</select></label><label>Attendance from<input type="date" value={startDate} onChange={e=>setStartDate(e.target.value)} /></label><label>Attendance to<input type="date" min={startDate || undefined} value={endDate} onChange={e=>setEndDate(e.target.value)}/></label></div><p className="p9-filter-help"><CalendarDays size={14}/> Date filters apply to attendance only. Historical marks have no assessment dates, so scores are filtered by program and semester.</p></section>

    {error && <div className="p9-error" role="alert"><AlertCircle size={18}/>{error}</div>}
    {loading && <div className="p9-loading"><span className="loader"/> Updating reports...</div>}

    {report && <>
      <div className="p9-metric-grid"><ReportStat icon={UsersRound} label="Students enrolled" value={number(stats.students)} sub="In the selected program"/><ReportStat icon={BookOpen} label="Recorded assessments" value={number(stats.assessments)} sub={`${number(stats.students_with_marks)} students with marks`} tone="blue"/><ReportStat icon={Target} label="Academic average" value={percent(stats.average_marks)} sub="Across recorded marks" tone="mint"/><ReportStat icon={ClipboardCheck} label="Attendance rate" value={percent(stats.attendance_rate)} sub={`${number(stats.attendance_records)} recorded sessions`} tone="amber"/></div>

      <div className="p9-visual-grid">
        <Panel icon={TrendingUp} title="Semester performance" description="Average score by semester · course filter applied" wide>
          {trend.length ? <div className="p9-chart"><ResponsiveContainer width="100%" height="100%"><AreaChart data={trend} margin={{top:14,right:18,left:-20,bottom:4}}><defs><linearGradient id="p9area" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor="#7665e9" stopOpacity={.23}/><stop offset="95%" stopColor="#7665e9" stopOpacity={.015}/></linearGradient></defs><CartesianGrid stroke="#eff0f6" strokeDasharray="4 4" vertical={false}/><XAxis dataKey="semester" tick={{fontSize:11,fill:'#7d8596'}} axisLine={false} tickLine={false}/><YAxis domain={[0,100]} tick={{fontSize:11,fill:'#8e96a6'}} axisLine={false} tickLine={false} tickFormatter={v=>`${v}%`}/><Tooltip formatter={v=>[percent(v),'Average score']}/><Area type="monotone" dataKey="average" stroke="#7665e9" strokeWidth={3} fill="url(#p9area)" activeDot={{r:6,stroke:'#fff',strokeWidth:2}} dot={{r:4,fill:'#7665e9'}}/></AreaChart></ResponsiveContainer></div> : <Empty message="Save marks under semesters to compare results."/>}
        </Panel>
        <Panel icon={ClipboardCheck} title="Attendance by month" description="Presence rate across filtered sessions">
          {months.length ? <div className="p9-chart"><ResponsiveContainer width="100%" height="100%"><BarChart data={months.slice(-10)} margin={{top:14,right:9,left:-21,bottom:4}}><CartesianGrid stroke="#f0f1f6" vertical={false} strokeDasharray="4 4"/><XAxis dataKey="label" axisLine={false} tickLine={false} tick={{fontSize:10,fill:'#8891a1'}}/><YAxis domain={[0,100]} axisLine={false} tickLine={false} tick={{fontSize:11,fill:'#8891a1'}} tickFormatter={v=>`${v}%`}/><Tooltip formatter={v=>[percent(v),'Attendance rate']}/><Bar dataKey="rate" radius={[5,5,0,0]} fill="#4fc8b2" maxBarSize={33}/></BarChart></ResponsiveContainer></div>:<Empty message="Record attendance in the selected date range to see a trend."/>}
        </Panel>
        <Panel icon={BookOpen} title="Subject performance" description="Highest-volume subjects and their average scores">
          {subjects.length ? <div className="p9-chart"><ResponsiveContainer width="100%" height="100%"><BarChart data={subjects} layout="vertical" margin={{top:10,right:24,left:4,bottom:5}}><CartesianGrid stroke="#eff0f6" horizontal={false} strokeDasharray="4 4"/><XAxis type="number" domain={[0,100]} tick={{fontSize:11,fill:'#8891a1'}} axisLine={false} tickLine={false}/><YAxis type="category" dataKey="name" width={110} tick={{fontSize:11,fill:'#697487'}} axisLine={false} tickLine={false} tickFormatter={v=>v.length>17?v.slice(0,16)+'…':v}/><Tooltip formatter={v=>[percent(v),'Average score']}/><Bar dataKey="average" radius={[0,5,5,0]} maxBarSize={21}>{subjects.map((row,i)=><Cell key={row.name} fill={PALETTE[i%PALETTE.length]}/>)}</Bar></BarChart></ResponsiveContainer></div>:<Empty message="Add subject marks to populate this chart."/>}
        </Panel>
        <Panel icon={Layers3} title="Grade distribution" description="Counts based on recorded assessments">
          {gradeCount ? <div className="p9-grade-list">{grades.map((g,i)=><div className="p9-grade-row" key={g.name}><b>{g.name}</b><span className="p9-grade-rail"><i style={{width:`${Math.round(100*g.count/gradeCount)}%`,background:PALETTE[i%PALETTE.length]}}/></span><strong>{g.count}</strong><small>{Math.round(100*g.count/gradeCount)}%</small></div>)}</div>:<Empty message="No assessment results match your report settings."/>}
        </Panel>
      </div>

      <section className="p9-panel p9-program-table"><div className="p9-panel-head"><div className="p9-panel-icon"><GraduationCap size={18}/></div><div><h3>Program performance</h3><p>Student enrollment, average marks, and attendance side by side</p></div></div><div className="p9-table-wrap"><table className="data-table"><thead><tr><th>PROGRAM</th><th>STUDENTS</th><th>AVG. MARKS</th><th>ATTENDANCE</th></tr></thead><tbody>{report.course_breakdown.map(row=><tr key={row.name}><td><strong>{row.name}</strong></td><td>{row.students}</td><td>{percent(row.average)}</td><td>{percent(row.attendance)}</td></tr>)}{!report.course_breakdown.length&&<tr><td colSpan="4" className="empty-row">No programs match your filters.</td></tr>}</tbody></table></div></section>

      <section className="p9-export-panel"><div><span className="p9-section-overline">DOWNLOAD CENTER</span><h2>Share your academic insights</h2><p>{canExport ? 'Generate PDF and CSV files from your current filters.' : 'Report exports are limited to administrators; you can still explore all charts.'}</p></div>{canExport && <div className="p9-export-controls"><button disabled={Boolean(exporting) || badDates} onClick={()=>download('pdf')} className="primary-btn"><FileText size={17}/>{exporting==='pdf'?'Generating...':'Download PDF'}</button><button disabled={Boolean(exporting) || badDates} onClick={()=>download('csv')} className="p9-secondary-btn"><Download size={17}/>{exporting==='csv'?'Generating...':'Program CSV'}</button><button disabled={Boolean(exporting)} onClick={onDownloadStudents} className="p9-secondary-btn"><Download size={17}/>Full student CSV</button><div className="p9-student-export"><select aria-label="Student for individual PDF report" value={studentId} onChange={e=>setStudentId(e.target.value)}><option value="">Select student for PDF...</option>{students.map(s=><option value={s.id} key={s.id}>{s.name} (#{s.id})</option>)}</select><button disabled={Boolean(exporting) || badDates || !studentId} onClick={()=>download('student')} className="p9-secondary-btn"><ArrowDownToLine size={17}/>Student PDF</button></div></div>}</section>
    </>}
    <div className="p9-explainer"><AlertCircle size={17}/><p><b>Report accuracy:</b> Missing marks or attendance are displayed as unavailable—not as 0%. Existing Phase 8 records appear in the <b>Unassigned</b> semester until re-entered under a selected semester.</p></div>
  </div>;
}
