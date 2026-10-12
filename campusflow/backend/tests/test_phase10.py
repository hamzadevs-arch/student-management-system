"""Phase 10 access-control and deterministic QA tests."""
from test_phase9 import project  # reuses realistic Phase 8 -> 9 database migration fixture


def ask(client, headers, question):
    return client.post('/api/assistant/ask', headers=headers, json={'question': question})


def test_auth_and_prompt_roles(project):
    client, main, admin, teacher = project
    assert client.get('/api/assistant/capabilities').status_code == 401
    assert client.post('/api/assistant/ask', json={'question':'Count students'}).status_code == 401
    a = client.get('/api/assistant/capabilities', headers=admin)
    t = client.get('/api/assistant/capabilities', headers=teacher)
    assert a.status_code == t.status_code == 200
    assert any('top 5 students' in x.lower() for x in a.json()['prompts'])
    assert not any('top 5 students' in x.lower() for x in t.json()['prompts'])
    assert a.json()['mode'] == 'local'


def test_real_data_aggregates_and_migrations(project):
    client, main, admin, teacher = project
    count = ask(client, teacher, 'How many students are enrolled?')
    assert count.status_code == 200
    assert count.json()['metrics'][0]['value'] == '2'
    assert count.json()['mode'] == 'local'
    course = ask(client, teacher, 'How many students in Computer Science?')
    assert course.json()['metrics'][0]['value'] == '1'
    avg = ask(client, teacher, 'What is the overall average score?')
    assert avg.json()['metrics'][0]['value'] == '80.0%'
    attendance = ask(client, teacher, 'What is the attendance rate?')
    assert attendance.json()['metrics'][0]['value'] == '100.0%'
    subj = ask(client, teacher, 'Which subject has the highest average marks?')
    assert subj.json()['rows'][0]['label'] == 'Python'
    semester = ask(client, teacher, 'Show Unassigned semester performance')
    assert semester.json()['metrics'][0]['value'] == '80.0%'
    enrolled = ask(client, teacher, 'How many students in Semester 4?')
    assert enrolled.json()['metrics'][0]['value'] == '0'
    assert 'records' in enrolled.json()['note']


def test_admin_individual_and_teacher_restricted(project):
    client, main, admin, teacher = project
    t = ask(client, teacher, 'Show Ali marks')
    assert t.status_code == 200
    assert t.json()['kind'] == 'restricted'
    assert '80' not in t.json()['answer']
    a = ask(client, admin, 'Show Ali marks')
    assert a.json()['kind'] == 'individual'
    assert a.json()['metrics'][0]['value'] == '80.0%'
    assert a.json()['rows'][0]['label'] == 'Python'
    att = ask(client, admin, 'Show Ali attendance')
    assert att.json()['metrics'][0]['value'] == '100.0%'
    t = ask(client, teacher, 'Who are the top 5 students by average marks?')
    assert t.json()['kind'] == 'restricted'
    a = ask(client, admin, 'Who are the top 5 students by average marks?')
    assert a.json()['rows'][0]['label'] == 'Ali'
    t = ask(client, teacher, 'Which students have attendance below 75%?')
    assert t.json()['kind'] == 'restricted'


def test_no_arbitrary_sql_and_no_data_writes(project):
    client, main, admin, teacher = project
    with main.db() as conn:
        before = conn.execute('SELECT COUNT(*) FROM students').fetchone()[0]
    for dangerous in ('DROP TABLE students;', "How many students'; DROP TABLE students; --", "SELECT * FROM users;", "admin' OR 1=1 --"):
        response = ask(client, teacher, dangerous)
        assert response.status_code == 200
        assert 'password_hash' not in response.text
    with main.db() as conn:
        after = conn.execute('SELECT COUNT(*) FROM students').fetchone()[0]
    assert before == after == 2
    assert ask(client, teacher, 'x').status_code == 422
    assert ask(client, teacher, 'x'*501).status_code == 422


def test_filtered_aggregates_and_low_attendance(project):
    client, main, admin, teacher = project
    client.post('/api/marks', headers=teacher,
                json={'student_id':11,'subject':'Python','marks':90,'semester':'Semester 4'})
    client.post('/api/attendance', headers=teacher,
                json={'student_id':11,'date':'2026-10-11','status':'A','semester':'Semester 4'})
    r = ask(client, teacher, 'Average marks in Semester 4 for Computer Science')
    assert r.json()['metrics'][0]['value'] == '90.0%'
    r = ask(client, teacher, 'How many students in Semester 4?')
    assert r.json()['metrics'][0]['value'] == '1'
    low = ask(client, admin, 'Which students have attendance below 75%?')
    assert low.json()['rows'][0]['label'] == 'Ali'
    no_filter = ask(client, admin, 'What is the attendance rate in Semester 4?')
    assert no_filter.json()['metrics'][0]['value'] == '0.0%'


def test_llm_never_called_with_student_records(project, monkeypatch):
    """Even with a key, individual/role restricted results cannot reach the LLM."""
    client, main, admin, teacher = project
    monkeypatch.setenv('OPENAI_API_KEY', 'test-secret')
    from academic_assistant import optionally_polish_aggregate
    individual = {'kind':'individual','answer':'Ali marks','metrics':[], 'rows':[], 'note':'', 'mode':'local'}
    assert optionally_polish_aggregate(individual)['mode'] == 'local'
    restricted = {'kind':'restricted','answer':'Access denied', 'metrics':[], 'rows':[], 'note':'', 'mode':'local'}
    assert optionally_polish_aggregate(restricted)['mode'] == 'local'
