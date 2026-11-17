import json
from pathlib import Path
from playwright.sync_api import sync_playwright
creds=json.loads(Path('.qa-ui.json').read_text())
with sync_playwright() as p:
 b=p.chromium.launch(channel='msedge',headless=True);page=b.new_page(viewport={'width':1440,'height':1000},reduced_motion='reduce');errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
 page.goto('http://127.0.0.1:8001');page.locator('#login-form [name=username]').fill('qa.admin');page.locator('#login-form [name=password]').fill(creds['qa.admin']);page.locator('#login-form button.primary').click();page.locator('[data-route=integration]').click();page.locator('#tcbs-preview-form').wait_for()
 assert page.locator('#tcbs-source option[value=live]').is_disabled()
 for resource in ['assets','cash','risk','quotes','history']:
  page.locator('#tcbs-resource').select_option(resource);page.locator('#tcbs-preview-button').click();page.locator('#tcbs-preview-output table').wait_for()
  assert 'Giả lập' in page.locator('#tcbs-preview-output').inner_text()
  assert page.locator('#tcbs-send-prices').count()==0
  assert page.locator('#tcbs-preview-output td.numeric').evaluate_all('(cells)=>cells.every(c=>getComputedStyle(c).textAlign==="center")')
 page.locator('#tcbs-resource').select_option('assets');page.locator('#tcbs-preview-button').click();page.locator('#tcbs-preview-output table').wait_for();assert '0,026' in page.locator('#tcbs-preview-output').inner_text();page.screenshot(path='shots/tcbs-desktop.png',full_page=True)
 for width in [1024,768,390,320]:
  page.set_viewport_size({'width':width,'height':844});assert page.evaluate('document.documentElement.scrollWidth<=innerWidth'),width
  if width==390:page.locator('#tcbs-workspace').screenshot(path='shots/tcbs-mobile.png')
 page.set_viewport_size({'width':1440,'height':1000})
 page.locator('#tcbs-source').select_option('upload');page.locator('#tcbs-resource').select_option('history');page.locator('#tcbs-payload').fill('{bad json');page.locator('#tcbs-preview-button').click();assert 'JSON' in page.locator('#tcbs-error').inner_text()
 payload={'ticker':'TCB','data':[{'close':26000,'tradingDate':'2026-11-12T17:00:00Z'}]}
 page.locator('#tcbs-payload').fill(json.dumps(payload));page.locator('#tcbs-preview-button').click();page.locator('#tcbs-send-prices').wait_for();assert '2026-11-13' in page.locator('#tcbs-preview-output').inner_text()
 page.locator('#tcbs-send-prices').click();page.locator('#tcbs-submit-result').filter(has_text='Đã tạo').wait_for();assert page.locator('#tcbs-send-prices').is_disabled()
 assert not errors,errors
 print('PASS: 5 sample resources, no credential/live false claim, centred numeric columns, JSON validation, history preview/submit, 320-1440 responsive, no JS exceptions')
 b.close()
