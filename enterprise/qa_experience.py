"""UI regression on an isolated seeded instance. Never run mutation checks on production."""
import json, os
from pathlib import Path
import httpx
from playwright.sync_api import sync_playwright
BASE=os.getenv('QA_BASE_URL','http://127.0.0.1:8001')
creds=json.loads(Path(os.getenv('QA_CREDENTIALS_FILE','.qa-ui.json')).read_text())

def api_client(username):
    c=httpx.Client(base_url=BASE)
    r=c.post('/api/login',json={'username':username,'password':creds[username]});r.raise_for_status()
    c.headers['X-CSRF-Token']=r.json()['csrf'];return c

maker=api_client('qa.risk'); checker=api_client('qa.checker')
# Prepare an isolated, auditable approval queue and enough rows to exercise pagination.
existing=maker.get('/api/records/incidents').json()
if len(existing)<22:
    for i in range(22):
        data=dict(title=f'QA incident {i:02}',category='data',severity='low',owner='UI tests',due='2026-12-01',status='open',loss=0,notes='Synthetic test fixture')
        r=maker.post('/api/records/incidents',json={'data':data});r.raise_for_status()
        checker.post('/api/approvals/'+r.json()['id']+'/approve',json={'reason':'Synthetic fixture'}).raise_for_status()
proposal=maker.post('/api/records/positions',json={'data':dict(symbol='QA-DIALOG',book='QA',sector='QA',type='equity',value=1,beta=1,duration=0,adv=1)});proposal.raise_for_status();proposal_id=proposal.json()['id']
with sync_playwright() as p:
    browser=p.chromium.launch(channel='msedge',headless=True)
    context=browser.new_context(viewport={'width':1440,'height':1000},reduced_motion='reduce')
    page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
    page.goto(BASE);page.locator('#login-form [name=username]').fill('qa.admin');page.locator('#login-form [name=password]').fill(creds['qa.admin']);page.locator('#login-form button.primary').click()
    page.locator('.overview-grid').wait_for();Path('shots').mkdir(exist_ok=True)
    page.screenshot(path='shots/enterprise-desktop.png',full_page=True)
    page.keyboard.press('Control+k');page.locator('#command-search').fill('margin')
    assert page.locator('#command-results a').count()==1
    page.locator('#command-results a').click();page.locator('#data-table').wait_for();assert page.locator('#title').inner_text()=='Tín dụng & margin'
    page.locator('[data-route=incidents]').click();page.locator('.table-pagination').wait_for()
    assert page.locator('#data-table tbody tr:visible').count()==20
    page.get_by_role('button',name='Trang sau',exact=True).click();assert 0<page.locator('#data-table tbody tr:visible').count()<20
    page.locator('#search').fill('QA incident 01');assert page.locator('#data-table tbody tr:visible').count()==1
    page.locator('#search').fill('no matching records');assert page.locator('#data-table tbody tr:visible').count()==0
    assert 'Không có kết quả phù hợp' in page.locator('.table-pagination').inner_text()
    page.locator('#search').fill('');page.locator('#data-table .sort-column').first.click();assert page.locator('#data-table th').first.get_attribute('aria-sort')=='ascending'
    page.locator('[data-route=approvals]').click();page.locator('[data-decide="'+proposal_id+'"][data-value=reject]').click()
    page.locator('#decision-dialog').wait_for();assert 'QA-DIALOG' in page.locator('#decision-detail').inner_text()
    page.screenshot(path='shots/enterprise-approval.png',full_page=True)
    page.locator('#decision-form [name=reason]').fill('Rejected isolated UI fixture after review')
    page.locator('#decision-submit').click();page.locator('#decision-dialog').wait_for(state='hidden')
    assert next(x for x in checker.get('/api/approvals').json() if x['id']==proposal_id)['status']=='rejected'
    for route in ['positions','market','stress','margin','counterparties','cashflows','capital','limits','incidents','approvals','reports','integration','users','audit','settings']:
        page.locator('[data-route='+route+']').click();page.locator('#content .panel').first.wait_for()
        assert 'Không thể tải dữ liệu' not in page.locator('#content').inner_text(),route
    page.locator('[data-route=positions]').click();page.locator('#add').click();assert page.locator('#fields .form-help').count()>0;page.locator('#cancel-dialog').click()
    for width in [1024,768,390,320]:
        page.set_viewport_size({'width':width,'height':900 if width>760 else 844})
        if width<=760:page.locator('#menu').click()
        page.locator('[data-route=overview]').click();page.locator('.overview-grid').wait_for()
        assert page.evaluate('document.documentElement.scrollWidth<=innerWidth'),width
        if width==390:
            page.locator('#toast').wait_for(state='hidden');page.screenshot(path='shots/enterprise-mobile.png',full_page=True)
    assert not errors,errors
    print('PASS: 15 modules; command search/keyboard; table sorting, filtering, pagination/empty state; decision dialog persists rejection; form help; 320/390/768/1024 widths; no JS exceptions')
    browser.close()
