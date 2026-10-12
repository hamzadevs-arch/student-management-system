"""Phase 11 ML lab regression tests: privacy, migration, demo and real data."""
from test_phase9 import project


def test_routes_require_admin(project):
    client, main, admin, teacher = project
    body = {"mode": "demo", "previous_score": 76, "attendance_rate": 88}
    sample = {"student_id": 11, "previous_score": 72, "attendance_rate": 80, "next_score": 78}
    for endpoint, method, payload in [
        ('/api/ml/overview', 'get', None),
        ('/api/ml/examples', 'post', sample),
        ('/api/ml/predict', 'post', body),
        ('/api/ml/examples/1', 'delete', None),
    ]:
        for headers, expected in [(None, 401), (teacher, 403)]:
            response = getattr(client, method)(endpoint, headers=headers, **({'json': payload} if payload else {}))
            assert response.status_code == expected, response.text
    assert client.get('/api/ml/overview', headers=admin).status_code == 200


def test_legacy_data_preserved_and_demo_clearly_synthetic(project):
    client, main, admin, teacher = project
    first = client.get('/api/ml/overview', headers=admin).json()
    assert first['examples'] == 0 and not first['ready']
    assert first['demo']['type'] == 'Synthetic sample data'
    with main.db() as conn:
        assert conn.execute('SELECT COUNT(*) FROM students').fetchone()[0] == 2
        assert conn.execute('SELECT COUNT(*) FROM marks').fetchone()[0] == 1
        assert conn.execute('SELECT COUNT(*) FROM attendance').fetchone()[0] == 1
        assert conn.execute('SELECT COUNT(*) FROM performance_examples').fetchone()[0] == 0
    payload = {"mode":"demo","previous_score":75.0,"attendance_rate":85.0}
    result = client.post('/api/ml/predict', headers=admin, json=payload)
    assert result.status_code == 200, result.text
    assert result.json()['mode'] == 'demo'
    assert 'invented sample outcomes' in result.json()['disclaimer']
    assert 0 <= result.json()['estimated_next_score'] <= 100
    assert result.json()['evaluation']['mae'] >= 0
    assert client.post('/api/ml/predict', headers=admin, json=payload).json() == result.json()
    assert client.post('/api/ml/predict', headers=admin, json={**payload, 'mode':'real'}).status_code == 409
    with main.db() as conn:
        assert conn.execute('SELECT COUNT(*) FROM performance_examples').fetchone()[0] == 0


def test_validate_and_record_historical_examples(project):
    client, main, admin, teacher = project
    good = {"student_id":11,"previous_score":70,"attendance_rate":82,"next_score":77}
    for update in [{'student_id':999},{'previous_score':-5},{'attendance_rate':120},{'next_score':101}]:
        response = client.post('/api/ml/examples', headers=admin, json={**good, **update})
        assert response.status_code == (404 if 'student_id' in update else 422)
    saved = client.post('/api/ml/examples', headers=admin,json=good)
    assert saved.status_code == 201, saved.text
    example_id = saved.json()['id']
    rows = client.get('/api/ml/overview', headers=admin).json()['example_rows']
    assert rows[0]['student_name'] == 'Ali'
    assert rows[0]['previous_score'] == 70
    assert client.delete(f'/api/ml/examples/{example_id}',headers=admin).status_code == 200
    assert client.delete(f'/api/ml/examples/{example_id}',headers=admin).status_code == 404
    assert client.get('/api/ml/overview',headers=admin).json()['examples'] == 0


def test_real_model_training_and_delete_student_cascades(project):
    client, main, admin, teacher = project
    with main.db() as conn:
        for i in range(13,17):
            conn.execute('INSERT INTO students(id,name,age,email,course) VALUES(?,?,?,?,?)',
                         (i,f'Learner {i}',20,'', 'Computer Science'))
    ids = [11, 12, 13, 14, 15, 16]
    for i in range(18):
        prev = (52 + i*2) % 101
        rate = 64 + (i * 3) % 35
        next_score = min(100, round(.7 * prev + .25 * rate + 5, 1))
        r=client.post('/api/ml/examples',headers=admin,json={
            'student_id':ids[i%6], 'previous_score':prev,
            'attendance_rate':rate, 'next_score':next_score})
        assert r.status_code == 201,r.text
    overview=client.get('/api/ml/overview',headers=admin).json()
    assert overview['examples'] == 18 and overview['students'] == 6 and overview['ready']
    assert overview['evaluation']['test_count'] > 0
    assert overview['evaluation']['mae'] >= 0
    answer=client.post('/api/ml/predict',headers=admin,json={
        'mode':'real','previous_score':70,'attendance_rate':90})
    assert answer.status_code==200,answer.text
    assert answer.json()['mode'] == 'real'
    assert 'historical outcomes' in answer.json()['disclaimer']
    assert 0 <= answer.json()['estimated_next_score'] <= 100
    assert client.delete('/api/students/16',headers=admin).status_code==200
    remaining=client.get('/api/ml/overview',headers=admin).json()
    assert remaining['examples']==15 and remaining['students']==5
    assert client.get('/api/students',headers=admin).status_code==200


def test_invalid_prediction_values(project):
    client,main,admin,teacher=project
    for bad in [-1,101]:
        assert client.post('/api/ml/predict',headers=admin,json={
            'previous_score':bad,'attendance_rate':80,'mode':'demo'}).status_code==422
        assert client.post('/api/ml/predict',headers=admin,json={
            'previous_score':70,'attendance_rate':bad,'mode':'demo'}).status_code==422
    assert client.post('/api/ml/predict',headers=admin,json={
            'previous_score':70,'attendance_rate':80,'mode':'arbitrary'}).status_code==422
