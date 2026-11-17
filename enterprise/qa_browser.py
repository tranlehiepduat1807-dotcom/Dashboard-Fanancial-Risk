import json
from pathlib import Path
from playwright.sync_api import sync_playwright
secrets=json.loads(Path('.qa-credentials.json').read_text())
with sync_playwright() as p:
    browser=p.chromium.launch(channel='msedge',headless=True)
    page=browser.new_page(viewport={'width':1440,'height':1000})
    errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
    page.goto('http://127.0.0.1:8000')
    page.locator('#login-form [name=username]').fill('duat.admin')
    page.locator('#login-form [name=password]').fill(secrets['duat.admin'])
    page.locator('#login-form button').click()
    page.locator('.kpis').wait_for()
    Path('shots').mkdir(exist_ok=True)
    page.screenshot(path='shots/enterprise-desktop.png',full_page=True)
    checks=[]
    for key in ['positions','market','stress','margin','counterparties','cashflows','capital','limits','incidents','approvals','reports','integration','users','audit','settings']:
        page.locator('[data-route='+key+']').click()
        page.locator('#content .panel').first.wait_for()
        assert 'Không thể tải dữ liệu' not in page.locator('#content').inner_text(),key
        checks.append(key)
    page.locator('[data-route=positions]').click();page.locator('#add').click()
    page.locator('#record-form [name=symbol]').fill('QA-POSITION')
    page.locator('#record-form [name=book]').fill('QA book')
    page.locator('#record-form [name=sector]').fill('QA sector')
    for name,val in dict(value=10,beta=1,duration=0,adv=3).items():page.locator('#record-form [name='+name+']').fill(str(val))
    page.locator('#record-form [type=submit]').click();page.locator('#editor').wait_for(state='hidden')
    page.locator('[data-route=approvals]').click();page.get_by_text('QA-POSITION',exact=False).first.wait_for(state='attached')
    assert 'duat.admin' in page.locator('#content').inner_text()
    page.set_viewport_size({'width':390,'height':844})
    page.locator('#menu').click();page.locator('[data-route=overview]').click();page.locator('.kpis').wait_for()
    assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
    page.screenshot(path='shots/enterprise-mobile.png',full_page=True)
    assert not errors,errors
    print('PASS: login, 15 modules, create proposal, approval queue, mobile menu, no page overflow, no JS exceptions')
    browser.close()
