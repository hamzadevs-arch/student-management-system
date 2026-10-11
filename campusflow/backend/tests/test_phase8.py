"""Run from backend/: python -m pytest -q tests/test_phase8.py"""
import importlib
import os
import sqlite3
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


@pytest.fixture()
def system(tmp_path, monkeypatch):
    database = tmp_path / 'old_students.db'
    # Simulate a database from phases 3–5; existing data must survive.
    conn = sqlite3.connect(database)
    conn.execute('CREATE TABLE students (id INTEGER PRIMARY KEY,name TEXT NOT NULL,age INTEGER,email TEXT,course TEXT)')
    conn.execute('INSERT INTO students VALUES(101, "Ali", 20, "ali@example.com", "CS")')
    conn.commit()
    conn.close()
    monkeypatch.setenv('STUDENTS_DB', str(database))
    import main
    importlib.reload(main)
    from security import hash_password
    with main.db() as db:
        db.execute('INSERT INTO users(username,password_hash,role) VALUES (?, ?, ?)',
                   ('adminuser', hash_password('AdminSecure123!'), 'admin'))
    return TestClient(main.app), main


def auth(client, username, password):
    r=client.post('/api/auth/login',json={'username':username,'password':password})
    assert r.status_code==200, r.text
    return {'Authorization':'Bearer '+r.json()['access_token']}


def test_auth_permissions_and_existing_data(system):
    client, main = system
    assert client.get('/api/auth/setup-status').json()['configured']
    assert client.get('/api/students').status_code == 401
    assert client.get('/api/dashboard').status_code == 401
    assert client.get('/api/reports/students.csv').status_code == 401
    assert client.post('/api/auth/login',json={'username':'adminuser','password':'wrong'}).status_code == 401
    admin=auth(client,'adminuser','AdminSecure123!')
    assert client.get('/api/auth/me',headers=admin).json()['role']=='admin'
    assert client.get('/api/students',headers=admin).json()[0]['name']=='Ali'
    teacher=client.post('/api/accounts',headers=admin,json={'username':'teacher.one','password':'TeacherSecure123!'})
    assert teacher.status_code==201, teacher.text
    teacher_id=teacher.json()['id']
    teacher_auth=auth(client,'teacher.one','TeacherSecure123!')
    assert client.get('/api/students',headers=teacher_auth).status_code==200
    assert client.get('/api/dashboard',headers=teacher_auth).status_code==200
    assert client.get('/api/marks',headers=teacher_auth).status_code==200
    assert client.get('/api/attendance',headers=teacher_auth).status_code==200
    assert client.post('/api/marks',headers=teacher_auth,json={'student_id':101,'subject':'Python','marks':91}).status_code==200
    assert client.post('/api/attendance',headers=teacher_auth,json={'student_id':101,'date':'2026-10-11','status':'P'}).status_code==200
    for response in [
        client.post('/api/students',headers=teacher_auth,json={'id':200,'name':'Sam','age':21,'course':'CS'}),
        client.put('/api/students/101',headers=teacher_auth,json={'id':101,'name':'New','age':22,'course':'CS'}),
        client.delete('/api/students/101',headers=teacher_auth),
        client.get('/api/reports/students.csv',headers=teacher_auth),
        client.get('/api/accounts',headers=teacher_auth),
        client.post('/api/accounts',headers=teacher_auth,json={'username':'hacker','password':'WhateverSecure123!'}),
    ]:
        assert response.status_code==403, response.text
    assert client.get('/api/reports/students.csv',headers=admin).status_code==200
    assert len(client.get('/api/accounts',headers=admin).json())==2
    assert client.patch(f'/api/accounts/{teacher_id}/status',headers=admin,json={'active':False}).status_code==200
    assert client.get('/api/students',headers=teacher_auth).status_code==401
    assert client.post('/api/auth/login',json={'username':'teacher.one','password':'TeacherSecure123!'}).status_code==401
    assert client.patch(f'/api/accounts/{teacher_id}/status',headers=admin,json={'active':True}).status_code==200
    teacher_auth=auth(client,'teacher.one','TeacherSecure123!')
    assert client.post('/api/auth/logout',headers=teacher_auth).status_code==200
    assert client.get('/api/dashboard',headers=teacher_auth).status_code==401
    assert client.get('/api/students',headers=admin).json()[0]['id']==101


def test_account_validation_and_token_expiry(system):
    client, main=system
    admin=auth(client,'adminuser','AdminSecure123!')
    assert client.post('/api/accounts',headers=admin,json={'username':'bad name','password':'TeacherSecure123!'}).status_code==422
    assert client.post('/api/accounts',headers=admin,json={'username':'teacher2','password':'weak'}).status_code==422
    assert client.post('/api/accounts',headers=admin,json={'username':'ADMINUSER','password':'TeacherSecure123!'}).status_code==409
    with main.db() as conn:
        conn.execute('UPDATE sessions SET expires_at=0')
    assert client.get('/api/auth/me',headers=admin).status_code==401


def test_lockout(system):
    client,main=system
    for _ in range(5):
        r=client.post('/api/auth/login',json={'username':'adminuser','password':'incorrect'})
        assert r.status_code==401
    assert client.post('/api/auth/login',json={'username':'adminuser','password':'AdminSecure123!'}).status_code==401
    with main.db() as conn:
        conn.execute('UPDATE users SET locked_until=0,attempts=0 WHERE username=?',('adminuser',))
    assert client.post('/api/auth/login',json={'username':'adminuser','password':'AdminSecure123!'}).status_code==200
