import os, tempfile
from pathlib import Path
os.environ['DATABASE_URL']='sqlite:///'+str(Path(tempfile.mkdtemp())/'test.db')
from fastapi.testclient import TestClient
from sqlalchemy import text
from app.main import app,bootstrap,engine,analytics,password_hash
from manage import seed
import pytest

@pytest.fixture(scope='module',autouse=True)
def setup():
    for role in ['admin','analyst','approver','viewer','integration']: bootstrap(role,'Test-only-password-123!',role,role)
    seed()

def client(role):
    c=TestClient(app);r=c.post('/api/login',json={'username':role,'password':'Test-only-password-123!'});assert r.status_code==200
    c.headers['X-CSRF-Token']=r.json()['csrf'];return c

def position(value=10): return dict(symbol='NEW',book='Test',sector='Test',type='equity',value=value,beta=1,duration=0,adv=5)
def test_auth_required(): assert TestClient(app).get('/api/analytics').status_code==401
def test_login_generic_failure(): assert TestClient(app).post('/api/login',json={'username':'missing','password':'x'}).status_code==401
def test_csrf():
    c=client('analyst');c.headers.pop('X-CSRF-Token');assert c.post('/api/records/positions',json={'data':position()}).status_code==403
def test_viewer_read_only(): assert client('viewer').post('/api/records/positions',json={'data':position()}).status_code==403
def test_maker_checker_and_version_conflict():
    maker=client('analyst');checker=client('approver')
    r=maker.post('/api/records/positions',json={'data':position()});assert r.status_code==200;aid=r.json()['id']
    assert maker.post('/api/approvals/'+aid+'/approve',json={'reason':'self'}).status_code==403
    assert not any(x['symbol']=='NEW' for x in maker.get('/api/records/positions').json())
    assert checker.post('/api/approvals/'+aid+'/approve',json={'reason':'Checked'}).status_code==200
    assert checker.post('/api/approvals/'+aid+'/approve',json={'reason':'again'}).status_code==409
    row=next(x for x in maker.get('/api/records/positions').json() if x['symbol']=='NEW')
    ids=[maker.post('/api/records/positions',json={'data':position(v),'id':row['id'],'version':row['version']}).json()['id'] for v in [11,12]]
    assert checker.post('/api/approvals/'+ids[0]+'/approve',json={'reason':'checked'}).status_code==200
    assert checker.post('/api/approvals/'+ids[1]+'/approve',json={'reason':'stale'}).status_code==409
    assert maker.post('/api/records/positions',json={'data':position(),'id':row['id'],'version':1}).status_code==409

def test_invalid_input_atomic_import():
    c=client('integration');bad=[position(),{**position(),'value':-1}]
    before=len(c.get('/api/approvals').json())
    assert c.post('/api/import/positions',json=bad,headers={'Idempotency-Key':'atomic-test-01'}).status_code==422
    assert len(c.get('/api/approvals').json())==before

def test_idempotency():
    c=client('integration');headers={'Idempotency-Key':'same-batch-123'}
    r=c.post('/api/import/positions',json=[position()],headers=headers);assert r.status_code==200
    assert c.post('/api/import/positions',json=[position()],headers=headers).json()==r.json()
    assert c.post('/api/import/positions',json=[position(15)],headers=headers).status_code==409

def test_duplicate_natural_key():
    c=client('analyst');checker=client('approver');aid=c.post('/api/records/positions',json={'data':position()}).json()['id']
    assert checker.post('/api/approvals/'+aid+'/approve',json={'reason':'duplicate'}).status_code==409

def test_analytics_margin_liquidity_capital():
    a=client('viewer').get('/api/analytics').json()
    x=next(x for x in a['margin'] if x['account']=='SAMPLE-001')
    assert x['adjusted']==pytest.approx(12.75);assert x['call']==pytest.approx(3.25);assert x['breach']
    assert a['capital']['far']==pytest.approx(180)
    assert a['cashflows'][1]['balance']==pytest.approx(-2)
    assert a['counterparties'][0]['utilization']==pytest.approx(110)

def test_var_known_sample():
    # Each daily return is -1%; portfolio value 100 => every loss = 1.
    with engine.begin() as db:
        records=list(db.execute(text('SELECT * FROM records')))
        db.execute(text("DELETE FROM records WHERE kind IN ('positions','prices')"))
        import json
        db.execute(text("INSERT INTO records VALUES ('known','positions',:d,1,'now')"),{'d':json.dumps({**position(100),'symbol':'K'})})
        for i in range(62): db.execute(text("INSERT INTO records VALUES (:id,'prices',:d,1,'now')"),{'id':'k'+str(i),'d':json.dumps({'symbol':'K','date':f'{i:03d}','close':100*.99**i})})
        a=analytics(db);assert a['var']==pytest.approx(1);assert a['es']==pytest.approx(1)
        db.execute(text("DELETE FROM records WHERE kind IN ('positions','prices')"))
        for r in records:
            if r.kind in ['positions','prices']: db.execute(text('INSERT INTO records VALUES (:id,:k,:d,:v,:t)'),dict(id=r.id,k=r.kind,d=r.data,v=r.version,t=r.updated))

def test_no_fabricated_var():
    a=client('viewer').get('/api/analytics').json();assert a['var'] is None # NEW has no prices

def test_export_csv_and_audit_permissions():
    c=client('viewer');r=c.get('/api/export/positions');assert r.status_code==200 and 'NEW' in r.text
    assert c.get('/api/audit').status_code==403
    assert any(x['action']=='export' for x in client('admin').get('/api/audit').json())
def test_user_creation_permissions():
    assert client('analyst').post('/api/users',json={}).status_code==403
    assert client('admin').post('/api/users',json={'username':'newuser','name':'Test','role':'viewer','password':'long-test-pass-123'}).status_code==200

def test_secure_cookie_and_headers():
    r=TestClient(app).post('/api/login',json={'username':'viewer','password':'Test-only-password-123!'})
    assert 'HttpOnly' in r.headers['set-cookie'] and 'SameSite=strict' in r.headers['set-cookie']
    assert "script-src 'self'" in r.headers['content-security-policy']

def test_logout_invalidates_session():
    c=client('viewer');assert c.post('/api/logout').status_code==200;assert c.get('/api/me').status_code==401

def test_flex_mapper_units_and_missing_fields():
    from connectors.flex_mapper import normalize
    spec={'rows_path':['rows'],'fields':{'debt':{'path':['debt_vnd'],'scale':'0.000000001'}}}
    assert normalize({'rows':[{'debt_vnd':'1234500000'}]},spec)==[{'debt':1.2345}]
    with pytest.raises(ValueError): normalize({'rows':[{}]},spec)

def test_lock_user_invalidates_session():
    c=client('integration');admin=client('admin')
    uid=next(x['id'] for x in admin.get('/api/users').json() if x['username']=='integration')
    assert admin.post('/api/users/'+uid+'/active',json={'active':False}).status_code==200
    assert c.get('/api/me').status_code==401
    assert admin.post('/api/users/'+uid+'/active',json={'active':True}).status_code==200

def test_report_audited():
    assert client('viewer').get('/api/report').status_code==200
    assert any(x['action']=='export_report' for x in client('admin').get('/api/audit').json())

def test_admin_cannot_self_approve():
    c=client('admin'); aid=c.post('/api/records/positions',json={'data':{**position(),'symbol':'SELF'}}).json()['id']
    assert c.post('/api/approvals/'+aid+'/approve',json={'reason':'self'}).status_code==403

def test_registration_requires_admin_activation():
    c=TestClient(app)
    r=c.post('/api/register',json={'username':'signup-user','name':'New User','password':'Signup-password-123','role':'admin'})
    assert r.status_code==200 and r.json()['status']=='pending'
    assert c.post('/api/login',json={'username':'signup-user','password':'Signup-password-123'}).status_code==401
    admin=client('admin');row=next(u for u in admin.get('/api/users').json() if u['username']=='signup-user')
    assert row['role']=='viewer' and row['active']==0
    assert admin.post('/api/users/'+row['id']+'/active',json={'active':True}).status_code==200
    assert c.post('/api/login',json={'username':'signup-user','password':'Signup-password-123'}).status_code==200

def test_report_uses_selected_confidence():
    c=client('viewer')
    assert c.get('/api/report?confidence=0.975&shock=-0.2').json()['confidence']==0.975
    assert c.get('/api/report?confidence=0.5').status_code==422
