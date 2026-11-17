"""Read-only TCBS iFlash adapter based on supplied v1.0.0 PDF, pp. 4, 16, 18-22, 35."""
import json, math, os, re, secrets, time
from datetime import datetime
from decimal import Decimal, InvalidOperation
from zoneinfo import ZoneInfo
import httpx
from fastapi import HTTPException, Request
from starlette.concurrency import run_in_threadpool
from sqlalchemy import text

BASE_URL='https://openapi.tcbs.com.vn'
CATALOG={
 'assets':dict(label='Tài sản cổ phiếu',path='/aion/v1/accounts/{account}/se',page=18),
 'cash':dict(label='Số dư tiền',path='/aion/v1/accounts/{account}/cashInvestments',page=18),
 'risk':dict(label='Rủi ro margin / Rtt',path='/hydros/v1/account/{account}/risk',page=16),
 'quotes':dict(label='Thông tin mã, giá',path='/tartarus/v1/tickerCommons',page=21),
 'history':dict(label='Lịch sử giá ngày',path='/nyx/v2/stock/bars-long-term',page=35),
}
SAMPLE={
 'assets':{'assets':[{'symbol':'TCB','quantity':1000,'avgPrice':24000,'marketValue':26000000},{'symbol':'FPT','quantity':100,'avgPrice':90000,'marketValue':9500000}]},
 'cash':{'totalCount':1,'pageSize':20,'pageIndex':1,'data':[{'accountNo':'DEMO','bodBalance':50000000,'cashBalance':45000000,'pp0forBF':40000000,'bankAvlBalanceBF':0}]},
 'risk':[{'accountNo':'DEMO','rtt':75,'outstanding':20000000,'accruedInterest':150000,'dueAmount':0,'overdueAmount':0,'totalFeeDebt':0,'riskPolicy':{'initialMargin':50,'maintenanceMargin':40,'liquidationMargin':35},'riskStatus':{'code':'DEMO','description':'Chỉ minh họa cấu trúc phản hồi, không phải đánh giá tài khoản thật'}}],
 'quotes':{'data':[{'symbol':'TCB','matchPrice':26000,'refPrice':25500,'ceilPrice':27250,'floorPrice':23750,'totalVol':1200000,'changePercent':1.96}]},
 'history':{'ticker':'TCB','data':[{'open':25000,'high':26200,'low':24900,'close':26000,'volume':1000000,'tradingDate':'2026-11-12T17:00:00Z'},{'open':26000,'high':26800,'low':25700,'close':26500,'volume':1200000,'tradingDate':'2026-11-15T17:00:00Z'}]},
}
def bad(message): raise HTTPException(422,message)
def number(value):
    if isinstance(value,bool): bad('Số liệu TCBS không được là boolean')
    try: d=Decimal(str(value))
    except (ValueError,InvalidOperation): bad('Phản hồi có giá trị không phải số')
    if not d.is_finite() or abs(d)>Decimal('1e18'): bad('Số liệu ngoài phạm vi hỗ trợ')
    return float(d)
def money(value):
    number(value)
    return float(Decimal(str(value))/Decimal('1000000000'))
def normalize(resource,payload,symbol=''):
    if resource=='risk': items=payload
    else:
        if not isinstance(payload,dict): bad('Phản hồi cần là JSON object')
        items=payload.get('assets' if resource=='assets' else 'data')
    if not isinstance(items,list) or len(items)>1000 or any(not isinstance(x,dict) for x in items): bad('Mảng dữ liệu TCBS không hợp lệ hoặc vượt 1.000 dòng')
    out=[]
    try:
        for x in items:
            if resource=='assets':
                qty=number(x['quantity']); value=money(x['marketValue'])
                if qty<0 or value<0 or not re.fullmatch(r'[A-Za-z0-9_-]{1,20}',x['symbol']): bad('Vị thế âm hoặc mã không hợp lệ; mô hình hiện hỗ trợ long-only')
                out.append(dict(symbol=x['symbol'],quantity=qty,avgPrice=number(x['avgPrice']),value=value))
            elif resource=='cash': out.append(dict(account=str(x['accountNo']),cash=money(x['cashBalance']),bod=money(x['bodBalance']),purchasingPower=money(x['pp0forBF'])))
            elif resource=='risk':
                out.append(dict(account=str(x['accountNo']),rtt=number(x['rtt']),principal=money(x['outstanding']),interest=money(x['accruedInterest']),overdue=money(x['overdueAmount']),due=money(x['dueAmount']),feeDebt=money(x['totalFeeDebt']),initial=number(x['riskPolicy']['initialMargin']),maintenance=number(x['riskPolicy']['maintenanceMargin']),liquidation=number(x['riskPolicy']['liquidationMargin']),status=str(x['riskStatus']['description'])))
            elif resource=='quotes': out.append(dict(symbol=str(x['symbol']),price=number(x['matchPrice']),reference=number(x['refPrice']),volume=number(x['totalVol'])))
            elif resource=='history':
                ticker=payload.get('ticker')
                if not isinstance(ticker,str) or not re.fullmatch(r'[A-Za-z0-9_-]{1,10}',ticker): bad('Thiếu ticker hợp lệ trong phản hồi nến')
                if symbol and ticker.upper()!=symbol.upper(): bad('Ticker trong phản hồi khác mã được yêu cầu')
                date=datetime.fromisoformat(x['tradingDate'].replace('Z','+00:00'))
                if date.tzinfo is None: bad('tradingDate phải có múi giờ')
                close=number(x['close'])
                if close<=0: bad('Giá đóng cửa cần lớn hơn 0')
                day=date.astimezone(ZoneInfo('Asia/Ho_Chi_Minh')).date()
                if day>=datetime.now(ZoneInfo('Asia/Ho_Chi_Minh')).date(): bad('Chỉ nhận nến ngày trước hôm nay để tránh dùng nến chưa đóng')
                out.append(dict(symbol=ticker,date=day.isoformat(),close=close))
    except (KeyError,TypeError,ValueError,AttributeError): bad('Phản hồi thiếu trường hoặc sai định dạng theo tài liệu TCBS v1.0.0')
    if resource=='history' and len({(r['symbol'],r['date']) for r in out})!=len(out): bad('Phản hồi chứa nhiều nến cho cùng ngày; chỉ nhận resolution D')
    if resource=='cash' and number(payload.get('totalCount',len(out)))>len(out): bad('Phản hồi số dư chưa đủ trang; cần đối soát phân trang trước khi sử dụng')
    return out

def fetch_readonly(resource,account,symbol,count):
    token=os.getenv('TCBS_BEARER_TOKEN','').strip()
    if not token: raise HTTPException(409,'Chưa cấu hình JWT TCBS trên máy chủ. Có thể dùng minh họa hoặc nhập JSON trước.')
    params={}
    if resource=='quotes': params={'tickers':symbol}
    if resource=='history': params=dict(ticker=symbol,type='stock',resolution='D',to=int(time.time()),countBack=count)
    try:
        with httpx.Client(base_url=BASE_URL,timeout=15,follow_redirects=False) as client:
            r=client.get(CATALOG[resource]['path'].format(account=account),params=params,headers={'Authorization':'Bearer '+token})
            if r.status_code in [401,403]: raise HTTPException(409,'TCBS từ chối xác thực/quyền truy cập. Quản trị viên cần kiểm tra JWT.')
            if r.status_code==429: raise HTTPException(503,'TCBS giới hạn yêu cầu. Vui lòng thử lại sau.')
            if r.status_code!=200: raise HTTPException(502,'TCBS trả về lỗi; chưa nhập dữ liệu vào hệ thống.')
            if len(r.content)>2_000_000: raise HTTPException(502,'Phản hồi TCBS vượt 2 MB')
            return r.json()
    except (httpx.HTTPError,ValueError): raise HTTPException(502,'Không thể đọc phản hồi TCBS. Kiểm tra kết nối và thử lại.')

def install(app,engine,authenticated,audit,now,validate):
    with engine.begin() as db:
        db.execute(text('CREATE TABLE IF NOT EXISTS provider_snapshots (id VARCHAR(64) PRIMARY KEY, owner VARCHAR(64), resource VARCHAR(30), source VARCHAR(30), data TEXT, created VARCHAR(60), submitted INTEGER DEFAULT 0)'))
    @app.get('/api/tcbs/status')
    def status(req:Request):
        authenticated(req)
        return dict(provider='TCBS iFlash OpenAPI',version='1.0.0',configured=bool(os.getenv('TCBS_BEARER_TOKEN','').strip()),base_url=BASE_URL,catalog=CATALOG,mode='read-only')
    @app.post('/api/tcbs/preview')
    async def preview(req:Request):
        user=authenticated(req,{'admin','analyst','integration'})
        raw=await req.body()
        if len(raw)>2_000_000: raise HTTPException(413,'Phản hồi tối đa 2 MB')
        try: body=json.loads(raw)
        except ValueError: bad('JSON không hợp lệ')
        if not isinstance(body,dict): bad('Yêu cầu cần là JSON object')
        resource=body.get('resource');source=body.get('source');account=str(body.get('account','')).strip();symbol=str(body.get('symbol','')).strip().upper()
        if resource not in CATALOG or source not in ['sample','upload','live']: bad('Nguồn hoặc loại dữ liệu không hợp lệ')
        if source=='live' and resource in ['assets','cash','risk'] and not re.fullmatch('[A-Za-z0-9]{1,30}',account): bad('Cần số tiểu khoản hợp lệ')
        if source=='live' and resource in ['quotes','history'] and not re.fullmatch('[A-Z0-9_-]{1,10}',symbol): bad('Cần mã chứng khoán 1–10 ký tự')
        try: count=int(body.get('count',100))
        except (ValueError,TypeError): bad('Số nến cần là số nguyên')
        if not 1<=count<=500: bad('Chỉ nhận 1–500 nến')
        payload=SAMPLE[resource] if source=='sample' else body.get('payload') if source=='upload' else await run_in_threadpool(fetch_readonly,resource,account,symbol,count)
        rows=normalize(resource,payload,symbol if source!='sample' else '')
        sid=secrets.token_hex(12)
        with engine.begin() as db:
            db.execute(text('INSERT INTO provider_snapshots(id,owner,resource,source,data,created,submitted) VALUES(:id,:owner,:r,:s,:d,:t,0)'),dict(id=sid,owner=user['id'],r=resource,s=source,d=json.dumps(rows,ensure_ascii=False),t=now()))
            audit(db,user['username'],'tcbs_preview',sid,{'resource':resource,'source':source,'rows':len(rows)})
        return dict(id=sid,resource=resource,source=source,rows=rows,created=now(),can_submit=resource=='history' and source!='sample',note='MINH HỌA — không phải dữ liệu tài khoản thật' if source=='sample' else 'Chưa được duyệt; phản hồi JSON tải lên chưa được xác minh nguồn' if source=='upload' else 'Đọc từ TCBS; chưa nhập vào dữ liệu đã phê duyệt')
    @app.post('/api/tcbs/snapshots/{sid}/submit')
    def submit(sid:str,req:Request):
        user=authenticated(req,{'admin','analyst','integration'})
        with engine.begin() as db:
            snapshot=db.execute(text('SELECT * FROM provider_snapshots WHERE id=:id AND owner=:u'),dict(id=sid,u=user['id'])).mappings().first()
            if not snapshot: raise HTTPException(404,'Không tìm thấy bản xem trước của bạn')
            if snapshot['source']=='sample' or snapshot['resource']!='history': raise HTTPException(422,'Chỉ gửi phê duyệt lịch sử giá từ live/JSON; bản minh họa không được nhập')
            data=json.loads(snapshot['data'])
            if not data: bad('Không có giá để gửi duyệt')
            if snapshot['submitted']: raise HTTPException(409,'Bản xem trước đã được gửi duyệt')
            changed=db.execute(text('UPDATE provider_snapshots SET submitted=1 WHERE id=:id AND submitted=0'),{'id':sid})
            if changed.rowcount!=1: raise HTTPException(409,'Bản xem trước vừa được gửi duyệt')
            ids=[];skipped=0
            known_prices={}
            for record in db.execute(text("SELECT id,data,version FROM records WHERE kind='prices'")):
                price=json.loads(record.data);known_prices[(price['symbol'],price['date'])]=record
            for row in data:
                item=validate('prices',row)
                # Preserve maker/checker and version checks when updating a known price.
                existing=known_prices.get((item['symbol'],item['date']))
                if existing and json.loads(existing.data)==item: skipped+=1;continue
                aid=secrets.token_hex(12);ids.append(aid)
                db.execute(text("INSERT INTO approvals(id,kind,record_id,data,base_version,maker,status,created) VALUES(:id,'prices',:rid,:d,:v,:u,'pending',:t)"),dict(id=aid,rid=existing.id if existing else secrets.token_hex(12),d=json.dumps(item),v=existing.version if existing else 0,u=user['username'],t=now()))
            audit(db,user['username'],'tcbs_submit',sid,{'source':snapshot['source'],'proposals':len(ids),'approval_ids':ids,'unchanged':skipped})
        return dict(status='pending' if ids else 'unchanged',count=len(ids),unchanged=skipped,approval_ids=ids)
