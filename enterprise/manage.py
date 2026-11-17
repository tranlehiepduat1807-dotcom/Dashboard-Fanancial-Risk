import sys
if hasattr(sys.stdout,"reconfigure"): sys.stdout.reconfigure(encoding="utf-8")
"""One-time bootstrap. Run python manage.py create-user or seed-sample."""
import argparse, getpass, json, math, random, secrets
from datetime import date, timedelta
from sqlalchemy import text
from app.main import bootstrap,engine,now,audit

def seed():
    with engine.begin() as db:
        if db.execute(text('SELECT COUNT(*) FROM records')).scalar(): raise SystemExit('Chỉ nạp mẫu vào cơ sở dữ liệu rỗng.')
        sample={
          'positions':[dict(symbol='SAMPLE-EQ-A',book='Tự doanh minh họa',sector='Ngân hàng',type='equity',value=28,beta=1.15,duration=0,adv=18),dict(symbol='SAMPLE-EQ-B',book='Tự doanh minh họa',sector='Công nghệ',type='equity',value=22,beta=1.05,duration=0,adv=14),dict(symbol='SAMPLE-BOND',book='Tự doanh minh họa',sector='Trái phiếu',type='bond',value=35,beta=0,duration=3.8,adv=3),dict(symbol='SAMPLE-CASH',book='Ngân quỹ minh họa',sector='Tiền',type='cash',value=15,beta=0,duration=0,adv=0)],
          'margin':[dict(account='SAMPLE-001',name='Khách hàng giả lập A',debt=8,collateral=15,haircut=.15,maintenance=.5,due='2026-12-01'),dict(account='SAMPLE-002',name='Khách hàng giả lập B',debt=3,collateral=12,haircut=.2,maintenance=.5,due='2026-12-15')],
          'counterparties':[dict(name='Đối tác giả lập A',rating='BBB (minh họa)',exposure=22,limit=20,due='2026-12-02')],
          'cashflows':[dict(date='2026-11-18',category='Thanh toán giả lập',inflow=3,outflow=12),dict(date='2026-11-19',category='Giải ngân giả lập',inflow=2,outflow=10),dict(date='2026-11-20',category='Thu hồi giả lập',inflow=18,outflow=3)],
          'limits':[dict(name='Tập trung một tài sản',metric='concentration_pct',threshold=25,severity='high',owner='Phòng QTRR'),dict(name='LTV margin',metric='margin_ltv_pct',threshold=50,severity='high',owner='Phòng tín dụng'),dict(name='Sử dụng hạn mức đối tác',metric='counterparty_pct',threshold=100,severity='high',owner='Phòng QTRR'),dict(name='Thiếu hụt thanh khoản',metric='liquidity_gap',threshold=0,severity='high',owner='Ngân quỹ'),dict(name='VaR / NAV',metric='var_pct',threshold=3,severity='medium',owner='Phòng QTRR')],
          'incidents':[dict(title='Chậm đối soát nguồn giá minh họa',category='data',severity='medium',owner='Vận hành dữ liệu',due='2026-11-20',status='investigating',loss=0,notes='Dữ liệu giả lập để thử quy trình xử lý.')],
          'capital':[dict(date='2026-11-16',available=180,market=35,settlement=45,operational=20)],'prices':[]}
        rng=random.Random(732)
        for symbol,vol in [('SAMPLE-EQ-A',.018),('SAMPLE-EQ-B',.023),('SAMPLE-BOND',.002)]:
            close=100
            for i in range(260):
                close*=math.exp(rng.gauss(0,vol));sample['prices'].append(dict(date=(date(2025,11,1)+timedelta(days=i)).isoformat(),symbol=symbol,close=round(close,5)))
        for kind,items in sample.items():
            for item in items: db.execute(text('INSERT INTO records(id,kind,data,version,updated) VALUES(:id,:k,:d,1,:t)'),dict(id=secrets.token_hex(12),k=kind,d=json.dumps(item,ensure_ascii=False),t=now()))
        audit(db,'bootstrap','seed_sample','database',{'source':'SYNTHETIC; not market data','counts':{k:len(v) for k,v in sample.items()}})
    print('Đã nạp dữ liệu giả lập. Không phải dữ liệu thị trường thực.')
if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('command',choices=['create-user','seed-sample']);args=parser.parse_args()
    if args.command=='seed-sample': seed()
    else:
        username=input('Tên đăng nhập: ').strip();name=input('Họ tên: ').strip();role=input('Vai trò [admin/analyst/approver/viewer/integration]: ').strip()
        if role not in {'admin','analyst','approver','viewer','integration'}: raise SystemExit('Vai trò không hợp lệ')
        password=getpass.getpass('Mật khẩu (>=12 ký tự): ')
        if password!=getpass.getpass('Nhập lại mật khẩu: '): raise SystemExit('Không trùng mật khẩu')
        bootstrap(username,password,role,name);print('Đã tạo tài khoản.')
