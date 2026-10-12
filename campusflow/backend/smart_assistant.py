"""Phase 13: local LLM intent recognition + vetted, live, read-only SQLite tools.

The language model NEVER writes SQL, directly queries tables, or invents factual
answers. It selects from a fixed set of tools. Every question is answered using
fresh database records at request time, using role-gated parameterized SELECTs.
"""
from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.parse
import urllib.request
from datetime import date

from academic_assistant import PROMPTS, ADMIN_PROMPTS, answer_question

TOOLS = ('overview', 'search_student', 'student_profile', 'student_marks',
         'student_attendance', 'subject_average', 'program_performance',
         'low_attendance', 'top_students', 'upcoming_events', 'help')
PROMPT_EXAMPLES = [
    'How many students are enrolled?',
    'Compare average marks by program',
    'What is the overall attendance rate?',
    'Which subjects have the highest averages?',
    'What academic events are coming up?',
    'Show performance in Semester 3',
]
ADMIN_EXAMPLES = [
    'Find a student named Hamza',
    'What marks did that student get?',
    'Which students have attendance below 75%?',
    'Who are the top 5 students?',
]
SYSTEM_PROMPT = """You are an intent classifier for an academic dashboard. Respond ONLY with JSON:
{"tool":"one of: overview, search_student, student_profile, student_marks, student_attendance, subject_average, program_performance, low_attendance, top_students, upcoming_events, help", "args":{"name":"optional student name", "student_id":null, "course":"optional program name", "semester":"optional semester e.g. Semester 3", "subject":"optional subject", "threshold":75, "limit":5}}
Pick exactly ONE tool to answer the current user question. Do not produce data, answers,
SQL, other tools or instructions. For marks/attendance of a named student choose
student_marks/student_attendance and place name in args.name. If the question says
'he', 'her', 'his', 'that student' without a name, use the provided contextual
student_id. General attendance is overview; a student's attendance is student_attendance.
Academic deadlines and holidays use upcoming_events. Out-of-scope uses help.
"""


def provider():
    value = os.getenv('CAMPUSFLOW_AI_PROVIDER', 'rules').strip().lower()
    return value if value in ('ollama', 'openai', 'rules') else 'rules'


def ollama_url():
    url = os.getenv('CAMPUSFLOW_OLLAMA_URL', 'http://127.0.0.1:11434').rstrip('/')
    parsed = urllib.parse.urlsplit(url)
    # SSRF defense: refuse arbitrary remote servers and URL user-info.
    if parsed.scheme != 'http' or parsed.hostname not in ('127.0.0.1', 'localhost', '::1') or parsed.username or parsed.password or parsed.path not in ('', '/') or parsed.query or parsed.fragment:
        return None
    return url


def provider_status():
    engine = provider()
    if engine == 'rules':
        return {'provider': 'rules', 'available': True, 'model': None}
    if engine == 'openai':
        enabled = bool(os.getenv('OPENAI_API_KEY') and os.getenv('CAMPUSFLOW_REMOTE_AI_CONSENT') == 'yes')
        return {'provider': 'openai', 'available': enabled, 'model': os.getenv('OPENAI_MODEL', 'gpt-4.1-mini') if enabled else None}
    url = ollama_url()
    if not url:
        return {'provider': 'ollama', 'available': False, 'model': None}
    try:
        with urllib.request.urlopen(url + '/api/tags', timeout=0.75) as res:
            info = json.load(res)
        names = [m.get('name', '') for m in info.get('models', [])]
        model = os.getenv('CAMPUSFLOW_OLLAMA_MODEL', 'llama3.2:3b')
        return {'provider': 'ollama', 'available': model in names or model.split(':')[0] in [n.split(':')[0] for n in names], 'model': model}
    except (OSError, ValueError, KeyError):
        return {'provider': 'ollama', 'available': False, 'model': None}


def _llm_route(question, context_student_id):
    engine = provider()
    if engine == 'rules':
        return None
    content = f'Question: {question}\nPrevious student ID for pronoun follow-ups: {context_student_id if context_student_id else "none"}'
    if engine == 'ollama':
        url = ollama_url()
        if url is None:
            return None
        data = {'model': os.getenv('CAMPUSFLOW_OLLAMA_MODEL','llama3.2:3b'),
                'stream': False, 'format': 'json',
                'options': {'temperature': 0, 'num_predict': 180},
                'messages': [{'role':'system','content':SYSTEM_PROMPT}, {'role':'user','content':content}]}
        req = urllib.request.Request(url + '/api/chat', data=json.dumps(data).encode(),
                                     headers={'Content-Type': 'application/json'}, method='POST')
        with urllib.request.urlopen(req, timeout=18) as resp:
            response = json.load(resp)
        output = response['message']['content']
    elif engine == 'openai':
        if not os.getenv('OPENAI_API_KEY') or os.getenv('CAMPUSFLOW_REMOTE_AI_CONSENT') != 'yes':
            return None
        # Explicit opt-in required because the user's question may contain personal information.
        body = {'model': os.getenv('OPENAI_MODEL','gpt-4.1-mini'), 'temperature': 0,
                'response_format': {'type':'json_object'},
                'messages': [{'role':'system','content':SYSTEM_PROMPT}, {'role':'user','content':content}]}
        req = urllib.request.Request('https://api.openai.com/v1/chat/completions',
            data=json.dumps(body).encode(),
            headers={'Content-Type':'application/json', 'Authorization':'Bearer ' + os.environ['OPENAI_API_KEY']},
            method='POST')
        with urllib.request.urlopen(req, timeout=20) as resp:
            output = json.load(resp)['choices'][0]['message']['content']
    else:
        return None
    parsed = json.loads(output)
    if not isinstance(parsed, dict) or parsed.get('tool') not in TOOLS or not isinstance(parsed.get('args', {}), dict):
        return None
    return {'tool': parsed['tool'], 'args': parsed.get('args', {})}


def _str_arg(args, key, limit=120):
    item = args.get(key)
    return str(item).strip()[:limit] if isinstance(item, (int, str)) else ''


def _int_arg(args, key, default, minimum, maximum):
    try:
        value = int(args.get(key, default))
        return min(max(value, minimum), maximum)
    except (ValueError, TypeError):
        return default


def _res(answer, kind, *, rows=None, metrics=None, note='', context_student_id=None, tool=None):
    return {'answer': answer, 'kind': kind, 'rows': rows or [], 'metrics': metrics or [],
            'note': note, 'mode': 'live_ai', 'context_student_id': context_student_id,
            'source': 'Live CampusFlow SQLite', 'tool': tool}


def _percent(v):
    return 'Not recorded' if v is None else f'{v:.1f}%'


def _student_lookup(conn, args, context_id):
    student_id = _int_arg(args, 'student_id', 0, 0, 999_999_999)
    name = _str_arg(args, 'name')
    if student_id:
        rows = conn.execute('SELECT id,name,age,email,course FROM students WHERE id=?',(student_id,)).fetchall()
    elif name:
        rows = conn.execute('SELECT id,name,age,email,course FROM students WHERE instr(lower(name),lower(?))>0 ORDER BY name,id LIMIT 12', (name,)).fetchall()
    elif context_id:
        rows = conn.execute('SELECT id,name,age,email,course FROM students WHERE id=?',(context_id,)).fetchall()
    else:
        rows = []
    return rows


def _route_tool(conn, planned, role, context_student_id):
    tool = planned['tool']
    args = planned['args']
    is_admin = role == 'admin'
    if tool in {'search_student','student_profile','student_marks','student_attendance','low_attendance','top_students'} and not is_admin:
        return _res('Individual student records and rankings are available to administrators only.', 'restricted', tool=tool)

    if tool in ('search_student','student_profile','student_marks','student_attendance'):
        matches = _student_lookup(conn, args, context_student_id if tool != 'search_student' else None)
        if not matches:
            return _res('No matching student was found. Try searching by name or student ID.', 'individual', tool=tool)
        if len(matches) > 1:
            return _res(f'I found {len(matches)} matching students. Please use the full name or student ID to narrow it down.',
                'individual', rows=[{'label':r['name'], 'value':str(r['id']), 'detail':r['course']} for r in matches[:10]],
                note='Results are limited to 10.', tool=tool)
        s = matches[0]
        sid = s['id']
        if tool in ('search_student', 'student_profile'):
            r = conn.execute('''SELECT
                (SELECT AVG(marks) FROM marks WHERE student_id=?) AS score,
                (SELECT COUNT(*) FROM marks WHERE student_id=?) AS nmarks,
                (SELECT 100.0*SUM(status='P')/NULLIF(COUNT(*),0) FROM attendance WHERE student_id=? AND status IN ('P','A')) AS attendance''', (sid,sid,sid)).fetchone()
            return _res(f"{s['name']} is enrolled in {s['course']} (Student ID {sid}). Current saved average: {_percent(r['score'])}; attendance: {_percent(r['attendance'])}.",
                'individual', metrics=[{'label':'Average score','value':_percent(r['score'])}, {'label':'Attendance','value':_percent(r['attendance'])}],
                rows=[{'label':'Program','value':s['course'],'detail':f'Student ID {sid}'}],
                context_student_id=sid, tool=tool)
        if tool == 'student_marks':
            rows = conn.execute('SELECT subject,semester,marks FROM marks WHERE student_id=? ORDER BY semester,subject LIMIT 30',(sid,)).fetchall()
            scores = [r['marks'] for r in rows if r['marks'] is not None]
            if not rows:
                return _res(f"{s['name']} does not have recorded marks yet.",'individual',context_student_id=sid,tool=tool)
            average = round(sum(scores)/len(scores),1) if scores else None
            return _res(f"{s['name']} has {len(rows)} recorded subject result(s), averaging {_percent(average)}.",
                'individual', rows=[{'label':r['subject'], 'value':_percent(r['marks']), 'detail':r['semester']} for r in rows],
                metrics=[{'label':'Average score','value':_percent(average)}],context_student_id=sid,tool=tool,
                note='Up to 30 entries shown. All figures come from saved marks.')
        rows = conn.execute("SELECT status,COUNT(*) AS count FROM attendance WHERE student_id=? AND status IN ('P','A') GROUP BY status",(sid,)).fetchall()
        by_status = {r['status']:r['count'] for r in rows}
        present,total = by_status.get('P',0), sum(by_status.values())
        return _res(f"{s['name']} attended {present} of {total} recorded sessions ({_percent(100*present/total if total else None)}).",
            'individual',metrics=[{'label':'Present','value':str(present)}, {'label':'Total sessions','value':str(total)}],
            context_student_id=sid,tool=tool)

    if tool == 'overview':
        row = conn.execute('''SELECT
            (SELECT COUNT(*) FROM students) AS students,
            (SELECT AVG(marks) FROM marks WHERE marks BETWEEN 0 AND 100) AS avg,
            (SELECT 100.0*SUM(status='P')/NULLIF(COUNT(*),0) FROM attendance WHERE status IN ('P','A')) AS attendance,
            (SELECT COUNT(*) FROM marks) AS assessments''').fetchone()
        return _res(f"There are {row['students']} enrolled students. The recorded average score is {_percent(row['avg'])}, with an attendance rate of {_percent(row['attendance'])}.",
            'aggregate', metrics=[{'label':'Enrolled','value':str(row['students'])}, {'label':'Average marks','value':_percent(row['avg'])},
            {'label':'Attendance','value':_percent(row['attendance'])}, {'label':'Marks entries','value':str(row['assessments'])}], tool=tool)
    if tool == 'subject_average':
        name = _str_arg(args, 'subject')
        rows = conn.execute('''SELECT subject,ROUND(AVG(marks),1) AS average,COUNT(*) AS n FROM marks
            WHERE marks BETWEEN 0 AND 100 AND (?='' OR lower(subject)=lower(?)) GROUP BY lower(subject)
            ORDER BY average DESC,n DESC LIMIT 15''',(name,name)).fetchall()
        return _res(f"{'Subject results' if name else 'Subjects ranked by average recorded marks'} ({len(rows)} shown).",
            'aggregate', rows=[{'label':r['subject'],'value':_percent(r['average']),'detail':f"{r['n']} assessments"} for r in rows],tool=tool)
    if tool == 'program_performance':
        course = _str_arg(args,'course')
        semester = _str_arg(args,'semester',60)
        # Only exact matches; never splice a model output into SQL.
        rows = conn.execute('''SELECT s.course,COUNT(DISTINCT s.id) AS students,ROUND(AVG(m.marks),1) AS average,
            COUNT(m.id) AS assessments FROM students s LEFT JOIN marks m ON m.student_id=s.id
              AND (?='' OR m.semester=?)
            WHERE (?='' OR lower(s.course)=lower(?)) GROUP BY s.course ORDER BY students DESC LIMIT 20''',
            (semester,semester,course,course)).fetchall()
        return _res('Current program performance from recorded marks' + (f' in {semester}' if semester else '') + '.',
            'aggregate',rows=[{'label':r['course'],'value':_percent(r['average']),
            'detail':f"{r['students']} students · {r['assessments']} assessments"} for r in rows],tool=tool)
    if tool == 'low_attendance':
        threshold = _int_arg(args,'threshold',75,1,100)
        rows = conn.execute('''SELECT s.id,s.name,COUNT(a.id) AS total,
            ROUND(100.0*SUM(a.status='P')/COUNT(a.id),1) AS rate FROM students s
            JOIN attendance a ON a.student_id=s.id AND a.status IN ('P','A')
            GROUP BY s.id,s.name HAVING rate < ? ORDER BY rate ASC LIMIT 20''',(threshold,)).fetchall()
        return _res(f"{len(rows)} students have recorded attendance below {threshold}% (up to 20 shown).",
            'individual',rows=[{'label':r['name'],'value':_percent(r['rate']), 'detail':f"ID {r['id']} · {r['total']} sessions"} for r in rows],tool=tool)
    if tool == 'top_students':
        count = _int_arg(args,'limit',5,1,20)
        rows = conn.execute('''SELECT s.name,s.id,ROUND(AVG(m.marks),1) AS average,COUNT(m.id) AS n
            FROM students s JOIN marks m ON m.student_id=s.id WHERE m.marks BETWEEN 0 AND 100
            GROUP BY s.id ORDER BY average DESC,n DESC LIMIT ?''',(count,)).fetchall()
        return _res(f"Top {len(rows)} students by recorded average marks.",'individual',
            rows=[{'label':r['name'],'value':_percent(r['average']),'detail':f"ID {r['id']} · {r['n']} assessments"} for r in rows],tool=tool)
    if tool == 'upcoming_events':
        today = date.today().isoformat()
        rows = conn.execute('''SELECT title,event_date,event_type,course FROM calendar_events
            WHERE event_date >= ? ORDER BY event_date ASC LIMIT 12''',(today,)).fetchall()
        return _res(f"I found {len(rows)} upcoming academic event(s) in the calendar.",
            'aggregate',rows=[{'label':r['title'],'value':r['event_date'],'detail':r['event_type'].title() + (' · '+r['course'] if r['course'] else '')} for r in rows],tool=tool)
    return _res('Ask about student enrollment, program performance, subject marks, attendance, or upcoming academic events.',
        'help',tool='help')


def _offline_plan(conn, question: str, context_student_id: int | None):
    """Keyword-and-entity resolver; explicit, deterministic, NO trained model.

    Only emits approved read-only tools. Fuzzy student search is done on current
    names in SQLite; user text never becomes SQL source code.
    """
    q = " ".join(question.lower().split())
    args = {}
    semesters = re.search(r"\b(?:semester|sem)\s*[-:#]?\s*(\d{1,2})\b", q)
    if semesters:
        args['semester'] = f"Semester {int(semesters.group(1))}"
    if 'unassigned' in q and 'semester' not in args:
        args['semester'] = 'Unassigned'
    count = re.search(r"\b(?:top|best|first)\s+(\d{1,2})\b", q)
    if count:
        args['limit'] = int(count.group(1))
    threshold = re.search(r"\b(?:below|under|less than)\s+(\d{1,3})\s*%", q)
    if threshold:
        args['threshold'] = int(threshold.group(1))
    name = None
    # Find complete names mentioned anywhere in text, using actual DB entries.
    for row in conn.execute('SELECT id,name FROM students ORDER BY length(name) DESC,id'):
        full = row['name'].strip()
        if full and re.search(r'(?<!\w)' + re.escape(full) + r'(?!\w)', q, re.I):
            name = full
            break
    if not name:
        # Short-name searches: "named Hamza", "find student Hamza".
        match = re.search(r"\b(?:named|called|name is|find|search(?: for)?|look up)\s+(?:a\s+|the\s+|any\s+)?(?:student\s+)?(?:named\s+|called\s+)?([a-z][a-z.' -]{0,55})",q)
        if match:
            name = re.split(r'\s+(?:in|on|at|from|among|with|who|whose|and)\b',match.group(1))[0].strip(" .?!,\"'")
    student_id = re.search(r"\b(?:student\s+id|student\s*#|id\s*#)\s*[:#]?\s*(\d{1,9})\b",q)
    if student_id:
        args['student_id'] = int(student_id.group(1))
    if name:
        args['name'] = name
    have_student = bool(name or student_id)
    follow_up = bool(context_student_id and re.search(r'\b(his|her|their|he|she|that student|this student|them)\b', q))
    if follow_up and not have_student:
        args['student_id'] = context_student_id
    individual = have_student or follow_up
    if re.search(r'\b(exams?|deadlines?|calendar|holidays?|upcoming events?|assignments?|meetings?)\b',q):
        return {'tool':'upcoming_events','args':args}
    if re.search(r'\b(top|best|rank|ranking|toppers?)\b',q) and re.search(r'\b(students?|scorers?|performers?)\b',q):
        return {'tool':'top_students','args':args}
    if re.search(r'\b(low|poor|below|under|less than|at risk)\b',q) and 'attend' in q:
        return {'tool':'low_attendance','args':args}
    if individual:
        if re.search(r'\b(marks?|grades?|scores?|results?|subjects?|assessments?)\b',q):
            tool='student_marks'
        elif 'attend' in q or 'absen' in q or 'present' in q:
            tool='student_attendance'
        else:
            tool='search_student'
        return {'tool':tool,'args':args}
    if re.search(r'\b(subjects?|courses? marks|subject average)\b',q) and re.search(r'\b(average|highest|marks|score|performance|subject)\b',q):
        return {'tool':'subject_average','args':args}
    if re.search(r'\b(programs?|courses?|degrees?|semesters?)\b',q) and re.search(r'\b(compare|comparison|performance|average|marks|scores?|semester)\b',q):
        for row in conn.execute('SELECT DISTINCT course FROM students WHERE course IS NOT NULL'):
            if row[0] and row[0].lower() in q:
                args['course'] = row[0]
                break
        return {'tool':'program_performance','args':args}
    if re.search(r'\b(how many students|student count|total students|enrolled|enrollment|overall|average score|average marks|attendance rate|attendance percentage)\b',q):
        return {'tool':'overview','args':args}
    return None


def ask(conn, question: str, role: str, context_student_id: int | None = None):
    """Intent comes from optional model; facts ALWAYS come from the current DB."""
    # An untrusted client context is never accepted for a teacher.
    context_student_id = context_student_id if role == 'admin' else None
    mode = 'local'
    try:
        plan = _llm_route(question, context_student_id)
        if plan:
            result = _route_tool(conn, plan, role, context_student_id)
            result['mode'] = 'ollama' if provider() == 'ollama' else 'openai'
            return result
    except (TimeoutError, OSError, urllib.error.URLError, ValueError, TypeError, KeyError, json.JSONDecodeError):
        pass
    # More flexible offline question recognition, always grounded in fresh SQLite.
    offline = _offline_plan(conn, question, context_student_id)
    # Respect proven Phase 10 interpretations and report shapes. Use new intent
    # router for student follow-ups and calendar questions that were previously
    # unsupported, and for explicit new student-profile lookups.
    is_follow_up = bool(context_student_id and re.search(r'\b(his|her|their|he|she|that student|this student|them)\b', question, re.I))
    is_calendar = bool(re.search(r'\b(calendar|events?|exams?|holidays?|assignments?|deadlines?)\b', question, re.I))
    is_profile = bool(re.search(r'\b(student profile|profile for|where is .+ enrolled)\b', question, re.I))
    if offline and (is_follow_up or is_calendar or is_profile):
        result = _route_tool(conn, offline, role, context_student_id)
        result['mode'] = 'local'
        return result
    # Legacy safe matching remains a fallback for less common requests.
    adjusted = question
    if context_student_id and re.search(r'\b(his|her|their|he|she|that student|this student)\b',question,re.I):
        row = conn.execute('SELECT name FROM students WHERE id=?',(context_student_id,)).fetchone()
        if row:
            adjusted = question + ' for ' + row['name']
    if re.search(r'\b(calendar|events?|exams?|holidays?|assignments?|deadlines?)\b',question,re.I):
        return {**_route_tool(conn,{'tool':'upcoming_events','args':{}},role,None), 'mode':mode}
    result = answer_question(conn, adjusted, role)
    result['mode'] = mode
    result['source'] = 'Live CampusFlow SQLite'
    result['context_student_id'] = context_student_id
    # Remember a uniquely identified student for later "their marks" questions,
    # while preserving previous Phase 10 answer wording and privacy semantics.
    if role == 'admin' and offline and offline['tool'] in ('search_student','student_profile','student_marks','student_attendance'):
        matches = _student_lookup(conn, offline['args'], None)
        if len(matches) == 1:
            result['context_student_id'] = matches[0]['id']
    return result
