"""Corrected Phase 13 offline integration smoke checks."""
from test_phase9 import project


def test_version_and_offline_default(project, monkeypatch):
    client, main, admin, teacher = project
    monkeypatch.delenv('CAMPUSFLOW_AI_PROVIDER', raising=False)
    version = client.get('/api/version')
    assert version.status_code == 200
    assert version.json() == {'project':'CampusFlow','phase':13,'edition':'Offline Smart Campus'}
    available = client.get('/api/assistant/capabilities', headers=teacher)
    assert available.status_code == 200
    assert available.json()['engine']['provider'] == 'rules'
    assert available.json()['mode'] == 'local'


def test_offline_name_then_pronoun_followup_uses_live_marks(project, monkeypatch):
    client, main, admin, teacher = project
    monkeypatch.setenv('CAMPUSFLOW_AI_PROVIDER','rules')
    name = client.post('/api/assistant/ask', headers=admin, json={'question':'Is there a student named Ali?'})
    assert name.status_code == 200 and name.json()['context_student_id'] == 11
    second = client.post('/api/assistant/ask', headers=admin, json={
        'question': 'What are his marks?', 'context_student_id': 11})
    assert second.status_code == 200
    assert second.json()['context_student_id'] == 11
    assert any(r['label']=='Python' for r in second.json()['rows'])
    before = [r['label'] for r in second.json()['rows']]
    client.post('/api/marks',headers=teacher,json={'student_id':11,'subject':'Cloud Computing','marks':92})
    after = client.post('/api/assistant/ask',headers=admin,json={'question':'Show his marks','context_student_id':11}).json()
    assert 'Cloud Computing' in [r['label'] for r in after['rows']]
    restricted = client.post('/api/assistant/ask',headers=teacher,json={'question':'Find student Ali'}).json()
    assert restricted['kind']=='restricted'


def test_new_endpoints_present_in_offline_build(project):
    client,main,admin,teacher=project
    assert client.get('/api/calendar',headers=teacher).status_code==200
    assert client.get('/api/branding',headers=admin).status_code==200
    assert client.post('/api/import/students/preview',headers=admin,files={
        'file':('students.csv',b'id,name,age,email,course\n903,Samira,20,samira@example.com,CS\n','text/csv')}).status_code==200
