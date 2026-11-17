"""Risk Management workspace. Amounts in VND billions; no live trading endpoints."""
import csv, hashlib, hmac, io, json, math, os, secrets, statistics, time
from datetime import datetime, timezone
from pathlib import Path
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

BASE = Path(__file__).parent
engine = create_engine(os.getenv('DATABASE_URL', 'sqlite:///./risk.db'), **({'connect_args': {'check_same_thread': False}} if os.getenv('DATABASE_URL', 'sqlite:').startswith('sqlite') else {}))
app = FastAPI(title='Risk Management Enterprise', version='1.0.0', docs_url=None, redoc_url=None)
KINDS = {'positions','margin','counterparties','cashflows','limits','incidents','prices','capital'}
ROLES = {'admin','analyst','approver','viewer','integration'}
ATTEMPTS = {}
def now(): return datetime.now(timezone.utc).isoformat()
def fail(code, message): raise HTTPException(code, message)
def password_hash(password, salt): return hashlib.pbkdf2_hmac('sha256', password.encode(), bytes.fromhex(salt), 310000).hex()
def audit(db, user, action, target, detail):
    db.execute(text('INSERT INTO audit(id,created,actor,action,target,detail) VALUES(:id,:created,:actor,:action,:target,:detail)'), dict(id=secrets.token_hex(12),created=now(),actor=user,action=action,target=target,detail=json.dumps(detail,ensure_ascii=False)))
def init():
    with engine.begin() as db:
        for sql in ['CREATE TABLE IF NOT EXISTS users (id VARCHAR(64) PRIMARY KEY, username VARCHAR(100) UNIQUE NOT NULL, name VARCHAR(200), role VARCHAR(30), salt VARCHAR(64), password VARCHAR(200), active INTEGER DEFAULT 1)', 'CREATE TABLE IF NOT EXISTS records (id VARCHAR(64) PRIMARY KEY, kind VARCHAR(30), data TEXT, version INTEGER DEFAULT 1, updated VARCHAR(60))', 'CREATE TABLE IF NOT EXISTS approvals (id VARCHAR(64) PRIMARY KEY, kind VARCHAR(30), record_id VARCHAR(64), data TEXT, base_version INTEGER, maker VARCHAR(100), checker VARCHAR(100), status VARCHAR(30), reason TEXT, created VARCHAR(60), decided VARCHAR(60))', 'CREATE TABLE IF NOT EXISTS audit (id VARCHAR(64) PRIMARY KEY, created VARCHAR(60), actor VARCHAR(100), action VARCHAR(100), target VARCHAR(100), detail TEXT)', 'CREATE TABLE IF NOT EXISTS business_keys (key VARCHAR(100) PRIMARY KEY, record_id VARCHAR(64))', 'CREATE TABLE IF NOT EXISTS sessions (token VARCHAR(100) PRIMARY KEY, user_id VARCHAR(64), csrf VARCHAR(100), expires DOUBLE PRECISION)', 'CREATE TABLE IF NOT EXISTS imports (id VARCHAR(100) PRIMARY KEY, digest VARCHAR(100), result TEXT)']:
            db.execute(text(sql))
        # No default or hardcoded account; bootstrap happens only through CLI.
init()
def bootstrap(username, password, role='admin', name='Quản trị viên'):
    if len(password)<12: raise ValueError('Mật khẩu cần ít nhất 12 ký tự')
    salt=secrets.token_hex(16)
    with engine.begin() as db:
        db.execute(text('INSERT INTO users(id,username,name,role,salt,password,active) VALUES(:id,:u,:n,:r,:s,:p,1)'),dict(id=secrets.token_hex(12),u=username,n=name,r=role,s=salt,p=password_hash(password,salt)))

def public_user(row): return {k:row[k] for k in ['id','username','name','role']}
def authenticated(req, allowed=None):
    token=req.cookies.get('risk_session','')
    with engine.connect() as db:
        entry=db.execute(text('SELECT * FROM sessions WHERE token=:t'),{'t':hashlib.sha256(token.encode()).hexdigest()}).mappings().first()
        if not entry or entry['expires']<time.time(): fail(401,'Phiên đăng nhập đã hết hạn')
        row=db.execute(text('SELECT * FROM users WHERE id=:id AND active=1'),{'id':entry['user_id']}).mappings().first()
    if not row: fail(401,'Tài khoản không còn hoạt động')
    if allowed and row['role'] not in allowed: fail(403,'Bạn không có quyền thực hiện thao tác này')
    if req.method not in ['GET','HEAD'] and not hmac.compare_digest(req.headers.get('x-csrf-token',''),entry['csrf']): fail(403,'CSRF token không hợp lệ')
    return public_user(row)

@app.middleware('http')
async def security(req, call_next):
    response=await call_next(req)
    response.headers['X-Content-Type-Options']='nosniff'
    response.headers['X-Frame-Options']='DENY'
    response.headers['Referrer-Policy']='same-origin'
    response.headers['Content-Security-Policy']="default-src 'self'; style-src 'self' 'unsafe-inline'; script-src 'self'; img-src 'self' data:; font-src 'self'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'"
    response.headers['Cache-Control']='no-store' if req.url.path.startswith('/api') else 'no-cache'
    return response

@app.get('/api/health')
def health():
    with engine.connect() as db: db.execute(text('SELECT 1'))
    return {'status':'ok','version':'1.0.0'}
@app.post('/api/login')
async def login(req:Request):
    data=await req.json(); key=(req.client.host,data.get('username',''))
    attempts=ATTEMPTS.setdefault(key,[]); attempts[:]=[t for t in attempts if t>time.time()-900]
    if len(attempts)>=5: fail(429,'Đã thử quá nhiều lần. Thử lại sau 15 phút.')
    with engine.begin() as db:
        row=db.execute(text('SELECT * FROM users WHERE username=:u AND active=1'),{'u':str(data.get('username',''))[:100]}).mappings().first()
        if not row or not hmac.compare_digest(password_hash(str(data.get('password','')),row['salt'] if row else '00'*16), row['password'] if row else 'x'*64):
            attempts.append(time.time()); fail(401,'Tên đăng nhập hoặc mật khẩu không đúng')
        token=secrets.token_urlsafe(40); csrf=secrets.token_urlsafe(30)
        db.execute(text('DELETE FROM sessions WHERE expires<:t'),{'t':time.time()})
        db.execute(text('INSERT INTO sessions(token,user_id,csrf,expires) VALUES(:t,:u,:c,:e)'),dict(t=hashlib.sha256(token.encode()).hexdigest(),u=row['id'],c=csrf,e=time.time()+28800))
        audit(db,row['username'],'login','session',{})
    ATTEMPTS.pop(key,None)
    response=Response(json.dumps({'user':public_user(row),'csrf':csrf}),media_type='application/json')
    response.set_cookie('risk_session',token,httponly=True,samesite='strict',secure=os.getenv('COOKIE_SECURE','0')=='1',max_age=28800)
    return response
@app.get('/api/me')
def me(req:Request):
    user=authenticated(req)
    with engine.connect() as db: csrf=db.execute(text('SELECT csrf FROM sessions WHERE token=:t'),{'t':hashlib.sha256(req.cookies['risk_session'].encode()).hexdigest()}).scalar_one()
    return {'user':user,'csrf':csrf}
@app.post('/api/logout')
def logout(req:Request):
    authenticated(req)
    with engine.begin() as db: db.execute(text('DELETE FROM sessions WHERE token=:t'),{'t':hashlib.sha256(req.cookies['risk_session'].encode()).hexdigest()})
    response=Response('{}',media_type='application/json'); response.delete_cookie('risk_session'); return response

# Explicit field schema: unknown fields rejected; numeric values must be finite.
SCHEMAS={
 'positions': {'symbol':'str','book':'str','sector':'str','type':['equity','bond','cash'],'value':'positive','beta':'number','duration':'positive','adv':'positive'},
 'margin': {'account':'str','name':'str','debt':'positive','collateral':'positive','haircut':'ratio','maintenance':'ratio','due':'date'},
 'counterparties': {'name':'str','rating':'str','exposure':'positive','limit':'positive','due':'date'},
 'cashflows': {'date':'date','category':'str','inflow':'positive','outflow':'positive'},
 'limits': {'name':'str','metric':['var_pct','concentration_pct','margin_ltv_pct','counterparty_pct','liquidity_gap'],'threshold':'positive','severity':['high','medium'],'owner':'str'},
 'incidents': {'title':'str','category':['operational','compliance','data','cyber'],'severity':['high','medium','low'],'owner':'str','due':'date','status':['open','investigating','resolved'],'loss':'positive','notes':'str'},
 'prices': {'date':'date','symbol':'str','close':'strictpositive'},
 'capital': {'date':'date','available':'positive','market':'positive','settlement':'positive','operational':'positive'}
}
def validate(kind, data):
    if kind not in SCHEMAS or not isinstance(data,dict): fail(422,'Loại dữ liệu không hợp lệ')
    schema=SCHEMAS[kind]
    if set(data)!=set(schema): fail(422,'Các trường bắt buộc: '+', '.join(schema))
    out={}
    for key,typ in schema.items():
        value=data[key]
        if isinstance(typ,list):
            if value not in typ: fail(422,f'{key}: chọn một trong '+', '.join(typ))
        elif typ in ['number','positive','strictpositive','ratio']:
            try: value=float(value)
            except (TypeError,ValueError): fail(422,f'{key}: cần giá trị số')
            if not math.isfinite(value) or abs(value)>1e12 or (typ!='number' and value<0) or (typ=='strictpositive' and value<=0) or (typ=='ratio' and value>1): fail(422,f'{key}: ngoài phạm vi hợp lệ')
        else:
            if not isinstance(value,str) or not value.strip() or len(value)>2000: fail(422,f'{key}: cần văn bản 1–2000 ký tự')
            value=value.strip()
            if typ=='date':
                try: datetime.strptime(value,'%Y-%m-%d')
                except ValueError: fail(422,f'{key}: cần ngày YYYY-MM-DD')
        out[key]=value
    if kind=='margin' and out['maintenance']<=0: fail(422,'LTV tối đa cần lớn hơn 0')
    if kind=='positions' and out['type']!='cash' and out['adv']<=0: fail(422,'ADV cần lớn hơn 0')
    return out

def rows(db,kind):
    return [dict(id=r.id,version=r.version,updated=r.updated,**json.loads(r.data)) for r in db.execute(text('SELECT * FROM records WHERE kind=:k ORDER BY updated DESC'),{'k':kind})]
@app.get('/api/schema')
def schema(req:Request): authenticated(req); return SCHEMAS
@app.get('/api/records/{kind}')
def records(kind:str,req:Request):
    authenticated(req)
    if kind not in KINDS: fail(404,'Không tìm thấy phân hệ')
    with engine.connect() as db: return rows(db,kind)

@app.post('/api/records/{kind}')
async def propose(kind:str,req:Request):
    user=authenticated(req,{'admin','analyst'}); body=await req.json(); data=validate(kind,body.get('data'))
    rid=body.get('id') or secrets.token_hex(12); aid=secrets.token_hex(12)
    with engine.begin() as db:
        old=db.execute(text('SELECT * FROM records WHERE id=:id AND kind=:k'),{'id':rid,'k':kind}).mappings().first()
        version=int(body.get('version',0))
        if version!=(old['version'] if old else 0): fail(409,'Dữ liệu đã thay đổi, hãy tải lại')
        db.execute(text("INSERT INTO approvals(id,kind,record_id,data,base_version,maker,status,created) VALUES(:id,:kind,:rid,:data,:v,:maker,'pending',:t)"),dict(id=aid,kind=kind,rid=rid,data=json.dumps(data,ensure_ascii=False),v=version,maker=user['username'],t=now()))
        audit(db,user['username'],'propose',aid,{'kind':kind,'record_id':rid,'data':data})
    return {'id':aid,'status':'pending','message':'Đã gửi đề nghị, chờ người khác phê duyệt'}
@app.get('/api/approvals')
def approvals(req:Request):
    authenticated(req)
    with engine.connect() as db: return [dict(r) for r in db.execute(text('SELECT * FROM approvals ORDER BY created DESC LIMIT 500')).mappings()]
@app.post('/api/approvals/{aid}/{decision}')
async def decide(aid:str,decision:str,req:Request):
    user=authenticated(req,{'admin','approver'}); body=await req.json(); reason=str(body.get('reason','')).strip()
    if decision not in ['approve','reject'] or not reason: fail(422,'Cần quyết định và lý do')
    with engine.begin() as db:
        r=db.execute(text('SELECT * FROM approvals WHERE id=:id'),{'id':aid}).mappings().first()
        if not r: fail(404,'Không tìm thấy đề nghị')
        if r['maker']==user['username']: fail(403,'Người lập không được tự duyệt')
        if r['status']!='pending': fail(409,'Đề nghị đã được xử lý')
        # Compare-and-swap ensures concurrent approval cannot apply twice.
        changed=db.execute(text("UPDATE approvals SET status=:s,checker=:u,reason=:reason,decided=:t WHERE id=:id AND status='pending'"),dict(s='approved' if decision=='approve' else 'rejected',u=user['username'],reason=reason[:2000],t=now(),id=aid))
        if changed.rowcount!=1: fail(409,'Đề nghị vừa được xử lý')
        if decision=='approve':
            approved_data=json.loads(r['data'])
            natural={'prices':['symbol','date'],'positions':['symbol','book'],'capital':['date'],'margin':['account'],'counterparties':['name'],'limits':['name']}.get(r['kind'],[])
            if natural:
                for existing in rows(db,r['kind']):
                    if existing['id']!=r['record_id'] and all(existing[k]==approved_data[k] for k in natural): fail(409,'Trùng khóa nghiệp vụ; hãy đề nghị sửa bản ghi đang có')
            if natural:
                key=hashlib.sha256(json.dumps([r['kind']]+[approved_data[k] for k in natural],ensure_ascii=False).encode()).hexdigest()
                db.execute(text('DELETE FROM business_keys WHERE record_id=:rid AND key<>:k'),{'rid':r['record_id'],'k':key})
                db.execute(text('INSERT INTO business_keys(key,record_id) VALUES(:k,:rid) ON CONFLICT(key) DO NOTHING'),{'k':key,'rid':r['record_id']})
                owner=db.execute(text('SELECT record_id FROM business_keys WHERE key=:k'),{'k':key}).scalar_one()
                if owner!=r['record_id']: fail(409,'Khóa nghiệp vụ đã được đề nghị khác phê duyệt')
            if r['base_version']==0:
                if db.execute(text('SELECT id FROM records WHERE id=:id'),{'id':r['record_id']}).first(): fail(409,'Bản ghi đã tồn tại')
                db.execute(text('INSERT INTO records(id,kind,data,version,updated) VALUES(:id,:k,:d,1,:t)'),dict(id=r['record_id'],k=r['kind'],d=r['data'],t=now()))
            else:
                changed=db.execute(text('UPDATE records SET data=:d,version=version+1,updated=:t WHERE id=:id AND version=:v'),dict(d=r['data'],t=now(),id=r['record_id'],v=r['base_version']))
                if changed.rowcount!=1: fail(409,'Bản gốc đã thay đổi; cần lập đề nghị mới')
        audit(db,user['username'],decision,aid,{'reason':reason,'before_version':r['base_version'],'data':json.loads(r['data'])})
    return {'status':'approved' if decision=='approve' else 'rejected'}

@app.post('/api/register')
async def register(req:Request):
    if 'application/json' not in req.headers.get('content-type',''): fail(415,'Cần dữ liệu JSON')
    key=('register',req.client.host); attempts=ATTEMPTS.setdefault(key,[])
    attempts[:]=[t for t in attempts if t>time.time()-3600]
    if len(attempts)>=5: fail(429,'Đã gửi nhiều yêu cầu. Vui lòng thử lại sau một giờ.')
    attempts.append(time.time())
    data=await req.json()
    if not isinstance(data,dict): fail(422,'Dữ liệu không hợp lệ')
    username=str(data.get('username','')).strip(); name=str(data.get('name','')).strip(); password=str(data.get('password',''))
    if not 3<=len(username)<=100 or not 1<=len(name)<=200 or not 12<=len(password)<=200: fail(422,'Cần tên đăng nhập 3–100 ký tự, họ tên và mật khẩu 12–200 ký tự')
    with engine.begin() as db:
        if db.execute(text('SELECT id FROM users WHERE username=:u'),{'u':username}).first(): fail(409,'Tên đăng nhập đã được sử dụng')
        salt=secrets.token_hex(16)
        db.execute(text("INSERT INTO users(id,username,name,role,salt,password,active) VALUES(:id,:u,:n,'viewer',:s,:p,0)"),dict(id=secrets.token_hex(12),u=username,n=name,s=salt,p=password_hash(password,salt)))
        audit(db,username,'request_account',username,{'role':'viewer','active':False})
    return {'status':'pending','message':'Đã gửi đăng ký. Quản trị viên cần duyệt kích hoạt trước khi bạn đăng nhập.'}

@app.get('/api/users')
def users(req:Request):
    authenticated(req,{'admin'})
    with engine.connect() as db: return [dict(r) for r in db.execute(text('SELECT id,username,name,role,active FROM users')).mappings()]
@app.post('/api/users')
async def create_user(req:Request):
    user=authenticated(req,{'admin'}); data=await req.json()
    role=data.get('role'); username=str(data.get('username','')).strip(); name=str(data.get('name','')).strip(); password=str(data.get('password',''))
    if role not in ROLES or not username or len(username)>100 or not name or len(password)<12: fail(422,'Cần tài khoản, họ tên, vai trò và mật khẩu ít nhất 12 ký tự')
    with engine.begin() as db:
        if db.execute(text('SELECT id FROM users WHERE username=:u'),{'u':username}).first(): fail(409,'Tài khoản đã tồn tại')
        salt=secrets.token_hex(16)
        db.execute(text('INSERT INTO users(id,username,name,role,salt,password,active) VALUES(:id,:u,:n,:r,:s,:p,1)'),dict(id=secrets.token_hex(12),u=username,n=name[:200],r=role,s=salt,p=password_hash(password,salt)))
        audit(db,user['username'],'create_user',username,{'role':role})
    return {'status':'created'}
@app.post('/api/password')
async def change_password(req:Request):
    u=authenticated(req); b=await req.json(); new=str(b.get('new',''))
    if len(new)<12: fail(422,'Mật khẩu mới cần ít nhất 12 ký tự')
    with engine.begin() as db:
        r=db.execute(text('SELECT * FROM users WHERE id=:id'),{'id':u['id']}).mappings().one()
        if not hmac.compare_digest(password_hash(str(b.get('old','')),r['salt']),r['password']): fail(403,'Mật khẩu hiện tại không đúng')
        salt=secrets.token_hex(16)
        db.execute(text('UPDATE users SET salt=:s,password=:p WHERE id=:id'),dict(s=salt,p=password_hash(new,salt),id=u['id']))
        audit(db,u['username'],'change_password',u['id'],{})
    with engine.begin() as db: db.execute(text('DELETE FROM sessions WHERE user_id=:u'),{'u':u['id']})
    return {'status':'updated','message':'Đăng nhập lại bằng mật khẩu mới'}
@app.post('/api/users/{uid}/active')
async def user_active(uid:str,req:Request):
    actor=authenticated(req,{'admin'}); body=await req.json()
    if uid==actor['id']: fail(422,'Không được tự khóa tài khoản đang dùng')
    active=body.get('active')
    if not isinstance(active,bool): fail(422,'Cần trạng thái true/false')
    with engine.begin() as db:
        if not db.execute(text('SELECT id FROM users WHERE id=:id'),{'id':uid}).first(): fail(404,'Không tìm thấy tài khoản')
        db.execute(text('UPDATE users SET active=:a WHERE id=:id'),dict(a=int(active),id=uid))
        db.execute(text('DELETE FROM sessions WHERE user_id=:id'),{'id':uid})
        audit(db,actor['username'],'user_active',uid,{'active':active})
    return {'active':active}

@app.get('/api/report')
def report(req:Request,confidence:float=.99,shock:float=-.15,rate:float=.02):
    user=authenticated(req)
    if confidence not in [.95,.975,.99] or not -.9<=shock<=1 or not -.2<=rate<=.2: fail(422,'Tham số mô hình ngoài phạm vi')
    with engine.begin() as db:
        result=analytics(db,confidence,shock,rate)
        audit(db,user['username'],'export_report','analytics',{'asof':result['asof'],'confidence':result['confidence']})
    return result

@app.get('/api/audit')
def audit_list(req:Request):
    authenticated(req,{'admin','approver'})
    with engine.connect() as db: return [dict(r) for r in db.execute(text('SELECT * FROM audit ORDER BY created DESC LIMIT 1000')).mappings()]

def analytics(db, confidence=.99, shock=-.15, rate=.02):
    p=rows(db,'positions'); nav=sum(x['value'] for x in p); prices=rows(db,'prices'); by={}
    for r in prices: by.setdefault(r['symbol'],{})[r['date']]=r['close']
    noncash=[x for x in p if x['type']!='cash']; dates=sorted(set.intersection(*(set(by.get(x['symbol'],{})) for x in noncash))) if noncash else []
    losses=[]
    for a,b in zip(dates,dates[1:]): losses.append(-sum(x['value']*(by[x['symbol']][b]/by[x['symbol']][a]-1) for x in noncash))
    sample=sorted(losses[-500:]); var=sample[math.ceil(len(sample)*confidence)-1] if len(sample)>=60 else None
    # Expected shortfall uses fractional probability mass at the quantile.
    es=None
    if var is not None:
        mass=len(sample)*(1-confidence); remain=mass; total=0
        for loss in reversed(sample):
            w=min(1,remain); total+=w*loss; remain-=w
            if remain<=1e-10: break
        es=total/mass
    margin=[]
    for x in rows(db,'margin'):
        adjusted=x['collateral']*(1-x['haircut']); ltv=x['debt']/adjusted*100 if adjusted else (100 if x['debt'] else 0)
        margin.append({**x,'adjusted':adjusted,'ltv':ltv,'call':max(0,x['debt']/x['maintenance']-adjusted) if x['maintenance'] else x['debt'],'breach':adjusted*x['maintenance']<x['debt']})
    cp=[{**x,'utilization':100*x['exposure']/x['limit'] if x['limit'] else (100 if x['exposure'] else 0),'breach':x['exposure']>x['limit']} for x in rows(db,'counterparties')]
    cash=sum(x['value'] for x in p if x['type']=='cash'); cumulative=cash; flows=[]
    for day in sorted({x['date'] for x in rows(db,'cashflows')}):
        items=[x for x in rows(db,'cashflows') if x['date']==day]; inflow=sum(x['inflow'] for x in items); outflow=sum(x['outflow'] for x in items); cumulative+=inflow-outflow
        flows.append({'date':day,'inflow':inflow,'outflow':outflow,'balance':cumulative})
    stress=[{'symbol':x['symbol'],'value':x['value'],'pnl':x['value']*x['beta']*shock if x['type']=='equity' else -x['value']*x['duration']*rate if x['type']=='bond' else 0} for x in p]
    positions=[{**x,'weight':100*x['value']/nav if nav else 0,'days':x['value']/(x['adv']*.1) if x['adv'] and x['type']!='cash' else 0} for x in p]
    metrics={'var_pct':100*var/nav if var is not None and nav else None,'concentration_pct':max([x['weight'] for x in positions if x['type']!='cash'],default=0),'margin_ltv_pct':max([x['ltv'] for x in margin],default=0),'counterparty_pct':max([x['utilization'] for x in cp],default=0),'liquidity_gap':max(0,-min([x['balance'] for x in flows],default=cash))}
    breaches=[{**x,'actual':metrics[x['metric']]} for x in rows(db,'limits') if metrics[x['metric']] is not None and metrics[x['metric']]>x['threshold']]
    capital=sorted(rows(db,'capital'),key=lambda x:x['date']); latest=capital[-1] if capital else None
    if latest:
        total=latest['market']+latest['settlement']+latest['operational']; latest={**latest,'total':total,'far':100*latest['available']/total if total else None}
    return dict(asof=now(),sample_data=any(x['symbol'].startswith('SAMPLE-') for x in p),nav=nav,var=var,es=es,price_asof=dates[-1] if dates else None,observations=len(sample),confidence=confidence,positions=positions,margin=margin,counterparties=cp,cashflows=flows,stress=stress,stress_total=sum(x['pnl'] for x in stress),metrics=metrics,breaches=breaches,capital=latest,losses=losses[-90:],data_status='Đủ 60 quan sát tối thiểu' if var is not None else 'Chưa đủ dữ liệu giá: cần ít nhất 61 ngày chung cho mọi tài sản',method='Historical VaR 1 ngày, tối đa 500 quan sát; mức tối thiểu 60; ES trung bình đuôi có trọng số. Stress dùng beta/duration tuyến tính. Đơn vị tỷ VND. Chính sách hạn mức do công ty phê duyệt.')
@app.get('/api/analytics')
def calculate(req:Request,confidence:float=.99,shock:float=-.15,rate:float=.02):
    authenticated(req)
    if confidence not in [.95,.975,.99] or not -.9<=shock<=1 or not -.2<=rate<=.2: fail(422,'Tham số mô hình ngoài phạm vi')
    with engine.connect() as db: return analytics(db,confidence,shock,rate)
@app.get('/api/export/{kind}')
def export(kind:str,req:Request):
    u=authenticated(req)
    if kind not in KINDS: fail(404,'Không tìm thấy dữ liệu')
    with engine.begin() as db:
        items=rows(db,kind); audit(db,u['username'],'export',kind,{'rows':len(items)})
    output=io.StringIO(); writer=csv.DictWriter(output,fieldnames=['id','version','updated',*SCHEMAS[kind]]); writer.writeheader()
    # Neutralize spreadsheet formulas in user-controlled text.
    writer.writerows([{k:("'"+v if isinstance(v,str) and v.startswith(('=','+','-','@','\t','\r')) else v) for k,v in x.items()} for x in items])
    return Response('\ufeff'+output.getvalue(),media_type='text/csv',headers={'Content-Disposition':f'attachment; filename="{kind}.csv"'})
@app.get('/api/template/{kind}')
def template(kind:str,req:Request):
    authenticated(req)
    if kind not in KINDS: fail(404,'Không tìm thấy mẫu')
    return Response(','.join(SCHEMAS[kind])+'\n',media_type='text/csv',headers={'Content-Disposition':f'attachment; filename="template-{kind}.csv"'})
@app.post('/api/import/{kind}')
async def import_records(kind:str,req:Request):
    user=authenticated(req,{'admin','analyst','integration'})
    if kind not in KINDS: fail(404,'Không tìm thấy phân hệ')
    raw=await req.body()
    if len(raw)>2_000_000: fail(413,'Tệp vượt quá 2 MB')
    key=req.headers.get('idempotency-key',''); digest=hashlib.sha256(kind.encode()+b':' +raw).hexdigest()
    if not 8<=len(key)<=100: fail(422,'Cần Idempotency-Key 8–100 ký tự')
    if 'text/csv' in req.headers.get('content-type',''):
        try: data=list(csv.DictReader(io.StringIO(raw.decode('utf-8-sig'))))
        except UnicodeError: fail(422,'CSV cần mã UTF-8')
    else:
        try: data=json.loads(raw)
        except (ValueError,UnicodeError): fail(422,'JSON không hợp lệ')
    if not isinstance(data,list) or not 1<=len(data)<=1000: fail(422,'Mỗi lô cần 1–1000 dòng')
    validated=[validate(kind,x) for x in data]
    with engine.begin() as db:
        old=db.execute(text('SELECT * FROM imports WHERE id=:id'),{'id':key}).mappings().first()
        if old:
            if old['digest']!=digest: fail(409,'Idempotency-Key đã dùng với nội dung khác')
            return json.loads(old['result'])
        ids=[]
        for item in validated:
            aid=secrets.token_hex(12); ids.append(aid)
            db.execute(text("INSERT INTO approvals(id,kind,record_id,data,base_version,maker,status,created) VALUES(:id,:k,:rid,:d,0,:u,'pending',:t)"),dict(id=aid,k=kind,rid=secrets.token_hex(12),d=json.dumps(item,ensure_ascii=False),u=user['username'],t=now()))
        result={'status':'pending','count':len(ids),'approval_ids':ids}
        db.execute(text('INSERT INTO imports(id,digest,result) VALUES(:id,:d,:r)'),dict(id=key,d=digest,r=json.dumps(result)))
        audit(db,user['username'],'import',kind,{'count':len(ids),'key':key,'digest':digest})
    return result

from app.tcbs import install as install_tcbs
install_tcbs(app,engine,authenticated,audit,now,validate)

@app.get('/')
def index(): return FileResponse(BASE/'static/index.html')
app.mount('/static',StaticFiles(directory=BASE/'static'),name='static')
