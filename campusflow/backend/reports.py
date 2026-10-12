"""Phase 9 reporting: filtered aggregates + administrator-only PDF/CSV exports.

Database access remains inside main.py's authenticated endpoint functions.
Date filters apply to dated attendance records; marks in legacy schema have no date.
"""
from __future__ import annotations

import csv
import io
from collections import Counter, defaultdict
from datetime import date, datetime
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (KeepTogether, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle)

BRAND = colors.HexColor('#6656D9')
PALE = colors.HexColor('#F5F3FF')
DARK = colors.HexColor('#25304B')
MUTED = colors.HexColor('#667085')
BORDER = colors.HexColor('#E7E9F1')


def _grade(score):
    if score >= 90: return 'A+'
    if score >= 80: return 'A'
    if score >= 70: return 'B'
    if score >= 60: return 'C'
    if score >= 50: return 'D'
    return 'F'


def _avg(values):
    return round(sum(values) / len(values), 1) if values else None


def _rate(rows):
    return round(100 * sum(r['status'] == 'P' for r in rows) / len(rows), 1) if rows else None


def _percent(value):
    return 'Not recorded' if value is None else f'{value:.1f}%'


def _where(prefix, course='', semester='', start_date=None, end_date=None, attendance=False):
    clauses = []
    params = []
    if course:
        clauses.append('s.course = ?')
        params.append(course)
    if semester:
        clauses.append(f'{prefix}.semester = ?')
        params.append(semester)
    if attendance:
        if start_date:
            clauses.append(f'{prefix}.date >= ?')
            params.append(start_date.isoformat())
        if end_date:
            clauses.append(f'{prefix}.date <= ?')
            params.append(end_date.isoformat())
    return (' WHERE ' + ' AND '.join(clauses) if clauses else ''), params


def report_analytics(conn, course='', semester='', start_date=None, end_date=None):
    """Return accurate nullable averages (missing records are not treated as zero)."""
    students = [dict(r) for r in conn.execute(
        'SELECT id,name,course FROM students WHERE (? = \'\' OR course=?) ORDER BY name',
        (course, course)).fetchall()]
    mark_where, mark_args = _where('m', course, semester)
    att_where, att_args = _where('a', course, semester, start_date, end_date, True)
    marks = [dict(r) for r in conn.execute(
        'SELECT m.student_id,m.subject,m.marks,m.semester,s.course FROM marks m '
        'JOIN students s ON s.id=m.student_id' + mark_where,
        mark_args).fetchall()]
    attendance = [dict(r) for r in conn.execute(
        'SELECT a.student_id,a.date,a.status,a.semester,s.course FROM attendance a '
        'JOIN students s ON s.id=a.student_id' + att_where,
        att_args).fetchall()]
    scores = [float(r['marks']) for r in marks if r['marks'] is not None and 0 <= r['marks'] <= 100]
    grades = Counter(_grade(n) for n in scores)
    subject_scores = defaultdict(list)
    subject_names = {}
    for row in marks:
        if row['marks'] is not None and 0 <= row['marks'] <= 100:
            name = row['subject'].strip()
            key = name.casefold()
            subject_names.setdefault(key, name)
            subject_scores[key].append(float(row['marks']))
    subjects = sorted(({'name': subject_names[k], 'average': _avg(v), 'count': len(v)}
                       for k, v in subject_scores.items()), key=lambda r: (-r['count'], r['name']))
    months = defaultdict(list)
    for row in attendance:
        if row['date'] and len(row['date']) >= 7:
            months[row['date'][:7]].append(row)
    attendance_monthly = [{'month': k, 'label': datetime.strptime(k, '%Y-%m').strftime('%b %Y'),
                           'rate': _rate(v), 'present': sum(r['status'] == 'P' for r in v),
                           'total': len(v)} for k, v in sorted(months.items()) if len(k) == 7 and k[4] == '-']
    # Comparison trend intentionally ignores the current semester selection, but retains course.
    all_term_where, term_args = _where('m', course)
    terms = defaultdict(list)
    for row in conn.execute('SELECT m.semester,m.marks FROM marks m JOIN students s ON s.id=m.student_id'
                            + all_term_where, term_args).fetchall():
        if row['marks'] is not None and 0 <= row['marks'] <= 100:
            terms[row['semester'] or 'Unassigned'].append(float(row['marks']))
    semester_trend = [{'semester': k, 'average': _avg(v), 'assessments': len(v)}
                      for k,v in sorted(terms.items())]
    programs = defaultdict(lambda: {'student_ids': set(), 'scores': [], 'attendance': []})
    for s in students:
        programs[s['course']]['student_ids'].add(s['id'])
    for m in marks:
        if m['marks'] is not None and 0 <= m['marks'] <= 100:
            programs[m['course']]['scores'].append(float(m['marks']))
    for a in attendance:
        programs[a['course']]['attendance'].append(a)
    course_breakdown = [{'name': name, 'students': len(v['student_ids']),
                         'average': _avg(v['scores']), 'attendance': _rate(v['attendance'])}
                        for name, v in sorted(programs.items(), key=lambda kv: (-len(kv[1]['student_ids']), kv[0]))]
    all_courses = [r[0] for r in conn.execute('SELECT DISTINCT course FROM students ORDER BY course').fetchall() if r[0]]
    all_semesters = [r[0] for r in conn.execute('SELECT DISTINCT semester FROM '
                     '(SELECT semester FROM marks UNION SELECT semester FROM attendance) ORDER BY semester').fetchall() if r[0]]
    return {
        'filters': {'course': course, 'semester': semester,
                    'start_date': start_date.isoformat() if start_date else '',
                    'end_date': end_date.isoformat() if end_date else ''},
        'courses': all_courses,
        'semesters': all_semesters,
        'stats': {
            'students': len(students),
            'students_with_marks': len({m['student_id'] for m in marks if m['marks'] is not None}),
            'assessments': len(scores),
            'average_marks': _avg(scores),
            'attendance_records': len(attendance),
            'attendance_rate': _rate(attendance),
        },
        'grades': [{'name': g, 'count': grades.get(g, 0)} for g in ['A+', 'A', 'B', 'C', 'D', 'F']],
        'subjects': subjects,
        'attendance_monthly': attendance_monthly,
        'semester_trend': semester_trend,
        'course_breakdown': course_breakdown,
    }


def student_report(conn, student_id, semester='', start_date=None, end_date=None):
    student_row = conn.execute('SELECT id,name,age,email,course FROM students WHERE id=?', (student_id,)).fetchone()
    if student_row is None:
        return None
    student = dict(student_row)
    where_m = ' AND m.semester=?' if semester else ''
    marks = [dict(r) for r in conn.execute(
        'SELECT m.subject,m.marks,m.semester FROM marks m WHERE m.student_id=?' + where_m +
        ' ORDER BY m.semester,m.subject', [student_id] + ([semester] if semester else [])).fetchall()]
    where_a = ''
    args = [student_id]
    if semester:
        where_a += ' AND a.semester=?'
        args.append(semester)
    if start_date:
        where_a += ' AND a.date>=?'
        args.append(start_date.isoformat())
    if end_date:
        where_a += ' AND a.date<=?'
        args.append(end_date.isoformat())
    attendance = [dict(r) for r in conn.execute(
        'SELECT a.date,a.status,a.semester FROM attendance a WHERE a.student_id=?' + where_a +
        ' ORDER BY a.date DESC', args).fetchall()]
    scores = [float(r['marks']) for r in marks if r['marks'] is not None and 0 <= r['marks'] <= 100]
    return {'student': student, 'marks': marks, 'attendance': attendance,
            'average': _avg(scores), 'attendance_rate': _rate(attendance)}


def _safe(value):
    return escape(str(value if value is not None else '—'))


def _styles():
    base = getSampleStyleSheet()
    base.add(ParagraphStyle(name='CFTitle', parent=base['Heading1'], fontName='Helvetica-Bold',
                            fontSize=21, leading=26, textColor=DARK, spaceAfter=7))
    base.add(ParagraphStyle(name='CFSubtitle', parent=base['Normal'], fontSize=9, leading=14,
                            textColor=MUTED, spaceAfter=17))
    base.add(ParagraphStyle(name='CFHeading', parent=base['Heading2'], fontName='Helvetica-Bold',
                            fontSize=12, leading=16, textColor=DARK, spaceBefore=18, spaceAfter=9))
    base.add(ParagraphStyle(name='CFCell', parent=base['Normal'], fontName='Helvetica',
                            fontSize=8, leading=11, textColor=DARK, wordWrap='CJK'))
    base.add(ParagraphStyle(name='CFCellHead', parent=base['CFCell'], fontName='Helvetica-Bold', textColor=colors.white))
    base.add(ParagraphStyle(name='CFSmall', parent=base['Normal'], fontSize=8, leading=12, textColor=MUTED))
    return base


def _table(headers, rows, widths, styles):
    head = [Paragraph(_safe(h), styles['CFCellHead']) for h in headers]
    data = [head] + [[Paragraph(_safe(v), styles['CFCell']) for v in row] for row in rows]
    if not rows:
        data.append([Paragraph('No recorded data',styles['CFSmall'])] + ['']*(len(headers)-1))
    table = Table(data, colWidths=widths, repeatRows=1, hAlign='LEFT')
    table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), BRAND),
        ('VALIGN',(0,0),(-1,-1),'TOP'),
        ('LEFTPADDING',(0,0),(-1,-1),9), ('RIGHTPADDING',(0,0),(-1,-1),9),
        ('TOPPADDING',(0,0),(-1,-1),8), ('BOTTOMPADDING',(0,0),(-1,-1),8),
        ('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#F8F9FD')]),
        ('LINEBELOW',(0,-1),(-1,-1),0.5,BORDER),
    ]))
    return table


def _pdf(story):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=19*mm, leftMargin=19*mm,
                            topMargin=20*mm,bottomMargin=18*mm, title='CampusFlow Academic Report',
                            author='CampusFlow')
    def decorate(canvas, doc):
        canvas.setStrokeColor(BORDER)
        canvas.setLineWidth(.6)
        canvas.line(19*mm, 15*mm, A4[0]-19*mm,15*mm)
        canvas.setFont('Helvetica',8)
        canvas.setFillColor(MUTED)
        canvas.drawString(19*mm, 11*mm,'CAMPUSFLOW  •  PRIVATE ACADEMIC REPORT')
        canvas.drawRightString(A4[0]-19*mm, 11*mm, f'Page {doc.page}')
    doc.build(story, onFirstPage=decorate, onLaterPages=decorate)
    return buffer.getvalue()


def summary_pdf(data):
    styles=_styles()
    story=[Paragraph('Academic performance report',styles['CFTitle']),
           Paragraph(f'Generated {date.today().isoformat()}  |  Course: {_safe(data["filters"]["course"] or "All")}'
                     f'  |  Semester: {_safe(data["filters"]["semester"] or "All")}',styles['CFSubtitle'])]
    f=data['filters']
    story.append(Paragraph('Attendance period: '+_safe(f['start_date'] or 'All dates')+' to '+_safe(f['end_date'] or 'All dates'),styles['CFSmall']))
    s=data['stats']
    story.append(Paragraph('At a glance',styles['CFHeading']))
    story.append(_table(['Students','Assessments','Average score','Attendance'],
        [[s['students'],s['assessments'],_percent(s['average_marks']),_percent(s['attendance_rate'])]],
        [41*mm,40*mm,46*mm,45*mm],styles))
    story.append(Paragraph('Subjects',styles['CFHeading']))
    story.append(_table(['Subject','Average marks','Results'],
       [[r['name'],_percent(r['average']),r['count']] for r in data['subjects']],
       [94*mm,43*mm,35*mm],styles))
    story.append(Paragraph('Programs',styles['CFHeading']))
    story.append(_table(['Program','Students','Average marks','Attendance'],
       [[r['name'],r['students'],_percent(r['average']),_percent(r['attendance'])] for r in data['course_breakdown']],
       [66*mm,31*mm,39*mm,36*mm],styles))
    story.append(Paragraph('Semester comparison',styles['CFHeading']))
    story.append(_table(['Semester','Average score','Assessments'],
        [[r['semester'],_percent(r['average']),r['assessments']] for r in data['semester_trend']],
        [78*mm,48*mm,46*mm],styles))
    story.append(Spacer(1,10))
    story.append(Paragraph('A missing average means no valid marks were recorded. Attendance date filters do not affect marks because legacy marks have no assessment date.',styles['CFSmall']))
    return _pdf(story)


def student_pdf(data, semester='', start_date=None, end_date=None):
    styles=_styles()
    s=data['student']
    story=[Paragraph('Student academic report',styles['CFTitle']),
           Paragraph('Generated '+date.today().isoformat()+'  |  CampusFlow student report',styles['CFSubtitle']),
           Paragraph('Student profile',styles['CFHeading'])]
    story.append(_table(['Student ID','Name','Program'],[[s['id'],s['name'],s['course']]],
                        [37*mm,65*mm,70*mm],styles))
    story.append(Spacer(1,12))
    story.append(Paragraph(f'Semester: {_safe(semester or "All")}  |  '
            f'Attendance dates: {_safe(start_date or "All")} to {_safe(end_date or "All")}',styles['CFSmall']))
    story.append(Paragraph('Academic summary',styles['CFHeading']))
    story.append(_table(['Average score','Attendance rate','Assessments','Sessions'],
      [[_percent(data['average']),_percent(data['attendance_rate']),len(data['marks']),len(data['attendance'])]],
      [43*mm,43*mm,43*mm,43*mm],styles))
    story.append(Paragraph('Subject results',styles['CFHeading']))
    story.append(_table(['Subject','Semester','Marks','Grade'],
      [[r['subject'],r['semester'],r['marks'],_grade(float(r['marks'])) if r['marks'] is not None else '—'] for r in data['marks']],
      [72*mm,48*mm,26*mm,26*mm],styles))
    story.append(Paragraph('Attendance entries (latest first)',styles['CFHeading']))
    story.append(_table(['Date','Semester','Status'],
      [[r['date'],r['semester'],'Present' if r['status']=='P' else 'Absent'] for r in data['attendance']],
      [50*mm,62*mm,60*mm],styles))
    story.append(Spacer(1,10))
    story.append(Paragraph('Attendance filters are based on session dates; assessment dates are not available for legacy records.',styles['CFSmall']))
    return _pdf(story)


def summary_csv(data):
    buffer=io.StringIO(newline='')
    writer=csv.writer(buffer)
    writer.writerow(['Program','Students','Average Marks (%)','Attendance Rate (%)'])
    for r in data['course_breakdown']:
        # Mitigate spreadsheet formula interpretation for untrusted program titles.
        title = r['name']
        if title and title.lstrip().startswith(('=','+','-','@')):
            title = "'"+title
        writer.writerow([title,r['students'],r['average'] if r['average'] is not None else '',
                         r['attendance'] if r['attendance'] is not None else ''])
    return buffer.getvalue()
