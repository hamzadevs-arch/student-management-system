"""Phase 9 reporting regression tests. Run from backend/: pytest -q tests/"""
import importlib
import sqlite3
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


@pytest.fixture()
def project(tmp_path, monkeypatch):
    path = tmp_path / 'students.db'
    # Older Phase 8 database, without semester columns.
    c=sqlite3.connect(path)
    c.executescript('''
        CREATE TABLE students(id INTEGER PRIMARY KEY,name TEXT NOT NULL,age INTEGER,email TEXT,course TEXT);
        CREATE TABLE marks(id INTEGER PRIMARY KEY AUTOINCREMENT, student_id INTEGER,subject TEXT,marks REAL);
        CREATE TABLE attendance(id INTEGER PRIMARY KEY AUTOINCREMENT, student_id INTEGER,date TEXT,status TEXT);
        INSERT INTO students VALUES (11,'Ali',20,'ali@example.com','Computer Science');
        INSERT INTO students VALUES (12,'Sara',20,'sara@example.com','Physics');
        INSERT INTO marks(student_id,subject,marks) VALUES (11,'Python',80);
        INSERT INTO attendance(student_id,date,status) VALUES (11,'2026-09-11','P');
    ''')
    c.commit(); c.close()
    monkeypatch.setenv('STUDENTS_DB',str(path))
    import main
    importlib.reload(main)
    from security import hash_password
    with main.db() as conn:
        conn.execute('INSERT INTO users(username,password_hash,role) VALUES(?,?,?)',
                     ('admin9', hash_password('StrongPassword123!'),'admin'))
        conn.execute('INSERT INTO users(username,password_hash,role) VALUES(?,?,?)',
                     ('teacher9', hash_password('AnotherStrongPass123!'),'teacher'))
    client=TestClient(main.app)
    def token(name,password):
        response=client.post('/api/auth/login',json={'username':name,'password':password})
        assert response.status_code==200,response.text
        return {'Authorization':'Bearer '+response.json()['access_token']}
    return client, main, token('admin9','StrongPassword123!'), token('teacher9','AnotherStrongPass123!')


def test_non_destructive_migration(project):
    client, main, admin, teacher = project
    with main.db() as conn:
        for table in ('marks','attendance'):
            cols=[r[1] for r in conn.execute(f'PRAGMA table_info({table})')]
            assert 'semester' in cols
            assert conn.execute(f'SELECT semester FROM {table}').fetchone()[0]=='Unassigned'
    assert client.get('/api/students',headers=admin).json()[0]['id']==12
    legacy=client.get('/api/reports/analytics?semester=Unassigned',headers=teacher).json()
    assert legacy['stats']['assessments']==1
    assert legacy['stats']['attendance_rate']==100.0


def test_semester_and_course_filters(project):
    client, main, admin, teacher=project
    for semester, mark in [('Semester 1',91),('Semester 2',60)]:
        response=client.post('/api/marks',headers=teacher,json={'student_id':11,'subject':'Python','marks':mark,'semester':semester})
        assert response.status_code==200,response.text
    assert client.post('/api/marks',headers=teacher,json={'student_id':11,'subject':'Python','marks':95,'semester':'Semester 1'}).status_code==200
    r=client.post('/api/attendance',headers=teacher,json={'student_id':11,'date':'2026-10-11','status':'A','semester':'Semester 1'})
    assert r.status_code==200,r.text
    assert client.post('/api/attendance',headers=teacher,json={'student_id':11,'date':'2026-10-12','status':'P','semester':'Semester 1'}).status_code==200
    obj=client.get('/api/reports/analytics?course=Computer%20Science&semester=Semester%201',headers=teacher).json()
    assert obj['stats']['students']==1
    assert obj['stats']['assessments']==1
    assert obj['stats']['average_marks']==95.0
    assert obj['stats']['attendance_rate']==50.0
    assert obj['semester_trend'] == [
        {'semester':'Semester 1','average':95.0,'assessments':1},
        {'semester':'Semester 2','average':60.0,'assessments':1},
        {'semester':'Unassigned','average':80.0,'assessments':1},
    ]
    filtered=client.get('/api/reports/analytics?semester=Semester%201&start_date=2026-10-12',headers=teacher).json()
    assert filtered['stats']['attendance_rate']==100.0
    assert filtered['stats']['average_marks']==95.0  # date filter does not change undated marks
    empty=client.get('/api/reports/analytics?course=Physics',headers=teacher).json()
    assert empty['stats']['students']==1
    assert empty['stats']['average_marks'] is None
    assert empty['stats']['attendance_rate'] is None
    assert client.get('/api/reports/analytics?start_date=2026-12-10&end_date=2026-10-01',headers=teacher).status_code==422
    assert client.get('/api/reports/analytics?start_date=not-a-date',headers=teacher).status_code==422


def test_export_roles_and_pdf_content(project):
    client, main, admin, teacher=project
    for url in ['/api/reports/summary.pdf', '/api/reports/summary.csv', '/api/reports/student/11.pdf']:
        assert client.get(url).status_code==401
        assert client.get(url,headers=teacher).status_code==403
    for url in ['/api/reports/summary.pdf', '/api/reports/student/11.pdf']:
        resp=client.get(url,headers=admin)
        assert resp.status_code==200,resp.text
        assert resp.content.startswith(b'%PDF')
        assert len(resp.content)>1500
        assert resp.headers['cache-control']=='no-store'
    csv_r=client.get('/api/reports/summary.csv',headers=admin)
    assert csv_r.status_code==200
    assert 'Computer Science' in csv_r.text
    assert client.get('/api/reports/student/999.pdf',headers=admin).status_code==404
    assert client.get('/api/reports/summary.pdf?start_date=2026-11-11&end_date=2026-10-01',headers=admin).status_code==422
    # Student account information was not changed by report generation.
    assert client.get('/api/auth/me',headers=admin).json()['username']=='admin9'
