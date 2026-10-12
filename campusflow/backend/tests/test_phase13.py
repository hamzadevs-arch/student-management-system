"""Phase 13: live questions, role separation, lossless upgrades, imports and reports."""
import io

from openpyxl import Workbook
from test_phase9 import project


def csv_upload():
    return ('students.csv', b'id,name,age,email,course\n401,Noor Khan,20,noor@example.com,Computer Science\n11,Existing Ali,20,other@example.com,Other Program\n402,Anas Iqbal,21,,Software Engineering\n', 'text/csv')


def test_import_permissions_preview_and_preservation(project):
    client, main, admin, teacher = project
    name, raw, mime = csv_upload()
    assert client.post('/api/import/students/preview', files={'file':(name,raw,mime)}).status_code==401
    assert client.post('/api/import/students/preview',headers=teacher,files={'file':(name,raw,mime)}).status_code==403
    preview = client.post('/api/import/students/preview',headers=admin,files={'file':(name,raw,mime)})
    assert preview.status_code==200, preview.text
    details=preview.json()
    assert details['ready_count']==2 and details['existing_count']==1 and details['invalid_count']==0
    assert client.get('/api/students',headers=admin).json().__len__()==2
    assert client.post('/api/import/students/commit',headers=teacher,files={'file':(name,raw,mime)}).status_code==403
    done = client.post('/api/import/students/commit',headers=admin,files={'file':(name,raw,mime)})
    assert done.status_code==200 and done.json()['imported']==2
    assert done.json()['skipped_existing']==1
    with main.db() as conn:
        assert conn.execute('SELECT name FROM students WHERE id=11').fetchone()[0]=='Ali'
        assert conn.execute('SELECT name FROM students WHERE id=401').fetchone()[0]=='Noor Khan'
        assert conn.execute('SELECT COUNT(*) FROM students').fetchone()[0]==4
    again=client.post('/api/import/students/commit',headers=admin,files={'file':(name,raw,mime)})
    assert again.json()['imported']==0


def test_import_excel_validation_is_atomic(project):
    client, main, admin, teacher = project
    wb=Workbook();sheet=wb.active
    sheet.append(['id','name','age','email','course'])
    sheet.append([501,'Mary',20,'mary@example.com','CS'])
    sheet.append([502,'Ali2',200,'ali2@example.com','CS'])
    buf=io.BytesIO();wb.save(buf)
    r=client.post('/api/import/students/preview',headers=admin,files={'file':('students.xlsx',buf.getvalue())})
    assert r.status_code==200 and r.json()['invalid_count']==1
    failed=client.post('/api/import/students/commit',headers=admin,files={'file':('students.xlsx',buf.getvalue())})
    assert failed.status_code==422
    with main.db() as conn:
        assert conn.execute('SELECT COUNT(*) FROM students WHERE id=501').fetchone()[0]==0
    # Formula is never silently evaluated as name/course.
    wb.active['B2']='=HYPERLINK("http://fake","hello")'
    buf=io.BytesIO();wb.save(buf)
    assert client.post('/api/import/students/commit',headers=admin,files={'file':('file.xlsx',buf.getvalue())}).status_code==422
    invalid=b'wrong,title\n1,Mary\n'
    assert client.post('/api/import/students/preview',headers=admin,files={'file':('bad.csv',invalid)}).status_code==422


def test_calendar_access_control_and_crud(project):
    client,main,admin,teacher=project
    event={'title':'Semester final examinations','event_date':'2027-04-14','event_type':'exam',
           'description':'Main hall','course':'Computer Science','semester':'Semester 3'}
    assert client.get('/api/calendar').status_code==401
    assert client.post('/api/calendar',headers=teacher,json=event).status_code==403
    created=client.post('/api/calendar',headers=admin,json=event)
    assert created.status_code==201,created.text
    eid=created.json()['id']
    listings=client.get('/api/calendar?start_date=2027-01-01&end_date=2027-12-31',headers=teacher)
    assert listings.status_code==200 and listings.json()[0]['title']==event['title']
    assert client.get('/api/calendar?start_date=2027-12-31&end_date=2027-01-01',headers=teacher).status_code==422
    assert client.put(f'/api/calendar/{eid}',headers=teacher,json=event).status_code==403
    assert client.put(f'/api/calendar/{eid}',headers=admin,json={**event,'title':'New event title'}).status_code==200
    assert client.delete(f'/api/calendar/{eid}',headers=teacher).status_code==403
    assert client.delete(f'/api/calendar/{eid}',headers=admin).status_code==200
    assert client.delete(f'/api/calendar/{eid}',headers=admin).status_code==404
    assert client.get('/api/calendar',headers=teacher).json()==[]


def test_pdf_branding_logo_and_data_preserved(project):
    client,main,admin,teacher=project
    assert client.get('/api/branding').status_code==401
    assert client.put('/api/branding',headers=teacher,json={'institution_name':'Not Allowed'}).status_code==403
    updated=client.put('/api/branding',headers=admin,json={
        'institution_name':'Demo Institute of Computing', 'department':'Registrar Office',
        'contact':'support@example.edu','footer':'For internal university use only'})
    assert updated.status_code==200,updated.text
    assert client.get('/api/branding',headers=teacher).json()['institution_name']=='Demo Institute of Computing'
    from PIL import Image
    img=Image.new('RGB',(30,30),'#6656d9');buffer=io.BytesIO();img.save(buffer,'PNG')
    uploaded=client.post('/api/branding/logo',headers=admin,files={'file':('logo.png',buffer.getvalue(),'image/png')})
    assert uploaded.status_code==200,uploaded.text
    assert client.get('/api/branding/logo',headers=teacher).content.startswith(b'\x89PNG')
    pdf=client.get('/api/reports/summary.pdf',headers=admin)
    assert pdf.status_code==200 and pdf.content.startswith(b'%PDF')
    student=client.get('/api/reports/student/11.pdf',headers=admin)
    assert student.status_code==200 and student.content.startswith(b'%PDF')
    with main.db() as conn:
        assert conn.execute('SELECT COUNT(*) FROM students').fetchone()[0]==2
        assert conn.execute('SELECT length(logo_png) FROM report_branding WHERE id=1').fetchone()[0] > 100
    assert client.delete('/api/branding/logo',headers=admin).status_code==200
    assert client.get('/api/branding/logo',headers=teacher).status_code==404


def test_ai_is_read_only_live_context_and_permissions(project,monkeypatch):
    client,main,admin,teacher=project
    import smart_assistant
    monkeypatch.setattr(smart_assistant,'_llm_route',lambda q,context: {'tool':'search_student','args':{'name':'Ali'}})
    monkeypatch.setattr(smart_assistant,'provider',lambda:'ollama')
    who=client.post('/api/assistant/ask',headers=admin,json={'question':'Where is Ali enrolled?'})
    assert who.status_code==200 and who.json()['context_student_id']==11
    assert who.json()['mode']=='ollama'
    teacher_answer=client.post('/api/assistant/ask',headers=teacher,json={'question':'Where is Ali enrolled?'})
    assert teacher_answer.json()['kind']=='restricted'
    monkeypatch.setattr(smart_assistant,'_llm_route',lambda q,context: {'tool':'student_marks','args':{'student_id':context}})
    first=client.post('/api/assistant/ask',headers=admin,json={'question':'What are his marks?', 'context_student_id':11}).json()
    assert first['kind']=='individual' and first['context_student_id']==11
    client.post('/api/marks',headers=teacher,json={'student_id':11,'subject':'Live Update','marks':95})
    second=client.post('/api/assistant/ask',headers=admin,json={'question':'What are his marks?', 'context_student_id':11}).json()
    assert any(r['label']=='Live Update' for r in second['rows'])
    with main.db() as conn:
        assert conn.execute('SELECT COUNT(*) FROM users').fetchone()[0]==2
        assert conn.execute('SELECT COUNT(*) FROM students').fetchone()[0]==2


def test_ai_provider_url_restriction_and_no_remote_by_default(monkeypatch):
    import smart_assistant
    monkeypatch.setenv('CAMPUSFLOW_OLLAMA_URL','http://169.254.169.254:80')
    assert smart_assistant.ollama_url() is None
    monkeypatch.setenv('CAMPUSFLOW_AI_PROVIDER','openai')
    monkeypatch.setenv('OPENAI_API_KEY','fake-token')
    monkeypatch.delenv('CAMPUSFLOW_REMOTE_AI_CONSENT',raising=False)
    assert smart_assistant.provider_status()['available'] is False
