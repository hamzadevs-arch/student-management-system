"""Deployment readiness: privacy, health check, optional demo viewer, idempotent bootstrap."""
from test_phase9 import project


def test_readiness_and_api_authentication(project):
    client, main, admin, teacher = project
    assert client.get('/api/health').json() == {'status': 'ok'}
    assert client.get('/api/students').status_code == 401
    assert client.get('/api/attendance').status_code == 401
    assert client.get('/api/marks').status_code == 401
    assert client.get('/api/path-does-not-exist').status_code == 404


def test_public_demo_viewer_is_read_only_but_regular_teacher_can_edit(project, monkeypatch):
    client, main, admin, teacher = project
    # Existing fixture teacher account is a valid teacher; make this one the demo.
    teacher_user = client.get('/api/auth/me', headers=teacher).json()
    monkeypatch.setenv('CAMPUSFLOW_PUBLIC_VIEWER_USERNAME', teacher_user['username'])
    me = client.get('/api/auth/me', headers=teacher)
    assert me.status_code == 200 and me.json()['read_only']
    for response in (
        client.post('/api/marks', headers=teacher, json={
            'student_id': 11, 'subject': 'Networks', 'marks': 90}),
        client.post('/api/attendance', headers=teacher, json={
            'student_id': 11, 'date': '2026-10-10', 'status': 'P'}),
        client.post('/api/import/students/commit', headers=teacher, files={
            'file': ('students.csv', b'id,name,age,email,course\\n902,Mina,19,m@example.com,CS\\n', 'text/csv')})
    ):
        assert response.status_code == 403
    assert client.get('/api/dashboard', headers=teacher).status_code == 200
    assert client.get('/api/calendar', headers=teacher).status_code == 200
    assert client.post('/api/marks', headers=admin, json={
        'student_id': 11, 'subject': 'Networks', 'marks': 89}).status_code == 200
    monkeypatch.delenv('CAMPUSFLOW_PUBLIC_VIEWER_USERNAME')
    assert client.post('/api/marks', headers=teacher, json={
        'student_id': 11, 'subject': 'Networks', 'marks': 92}).status_code == 200
