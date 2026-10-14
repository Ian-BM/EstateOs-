"""Responsive browser QA. Defaults to the local seeded demo; no record mutations."""
import json,os
from pathlib import Path
from playwright.sync_api import sync_playwright,expect
BASE=os.environ.get('ESTATE_QA_URL','http://127.0.0.1:8011')
ROOT=Path(__file__).resolve().parent.parent
WIDTHS=[320,375,430,768,1024,1440]

def main():
 results=[];errors=[]
 with sync_playwright() as p:
  browser=p.chromium.launch(executable_path='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',headless=True)
  context=browser.new_context(viewport={'width':375,'height':812})
  page=context.new_page();page.on('pageerror',lambda error:errors.append(str(error)))
  def fits(label):
   sizes=page.evaluate('({viewport:innerWidth,document:document.documentElement.scrollWidth})')
   assert sizes['document']<=sizes['viewport'],(label,sizes)
  for width in WIDTHS:
   page.set_viewport_size({'width':width,'height':900 if width>640 else 812})
   for route in ['/','/properties/','/properties/demo-property-01/','/agents/','/accounts/login/','/accounts/register/']:
    response=page.goto(BASE+route);assert response.status==200,(route,response.status);fits(f'{width}: {route}')
   page.goto(BASE+'/')
   if width<=640:
    bounds=page.locator('.search-button').bounding_box();hero=page.locator('.hero').bounding_box()
    assert bounds['y']+bounds['height']<=hero['y']+hero['height'],('search escapes hero',width)
    assert page.locator('.hero').evaluate('(el)=>el.scrollHeight<=el.clientHeight+1')
   if width==375:
    page.screenshot(path=str(ROOT/'artifacts/mobile-public-refined.png'))
   if width<=960:
    expect(page.locator('#public-nav')).not_to_be_visible();page.get_by_role('button',name='Menu',exact=False).click();expect(page.locator('#public-nav')).to_be_visible();expect(page.locator('.nav-backdrop')).to_be_visible()
    page.keyboard.press('Escape');expect(page.locator('.menu-toggle')).to_be_focused();expect(page.locator('#public-nav')).not_to_be_visible()
   results.append(f'Public pages, forms and hero fit at {width}px')
  page.goto(BASE+'/accounts/login/')
  page.get_by_label('Username:').fill(os.environ.get('ESTATE_QA_USERNAME','demo_admin'))
  page.get_by_label('Password:',exact=True).fill(os.environ.get('ESTATE_QA_PASSWORD','EstateDemo2026!'))
  page.get_by_role('button',name='Sign in →').click();expect(page.get_by_role('heading',name='Portfolio overview')).to_be_visible()
  for width in WIDTHS:
   page.set_viewport_size({'width':width,'height':900 if width>640 else 812})
   for route in ['/workspace/','/workspace/crm/','/workspace/records/properties/','/workspace/records/tenants/','/workspace/records/leads/','/workspace/records/leases/','/workspace/records/inspections/new/','/workspace/records/properties/new/','/workspace/pipeline/','/workspace/reports/','/workspace/performance/']:
    response=page.goto(BASE+route);assert response.status==200,(route,response.status);fits(f'{width}: {route}')
   page.goto(BASE+'/workspace/records/properties/')
   if width<=640:
    expect(page.locator('.records-table tbody tr').first).to_be_visible()
    assert page.locator('.records-table tbody td').first.get_attribute('data-label')=='Name'
    assert page.locator('.records-table tbody td').first.inner_text().strip()
    assert page.locator('.records-table tbody tr').first.evaluate('(el)=>getComputedStyle(el).display')=='block'
   if width==375:
    page.screenshot(path=str(ROOT/'artifacts/mobile-records-refined.png'))
    page.goto(BASE+'/workspace/');page.screenshot(path=str(ROOT/'artifacts/mobile-management-refined.png'))
    page.get_by_role('button',name='Toggle navigation').click();expect(page.locator('#workspace-nav')).to_have_class('sidebar open');expect(page.locator('.workspace-main')).to_have_attribute('inert','')
    expect(page.locator('.nav-backdrop')).to_be_visible();page.get_by_role('button',name='Close navigation',exact=True).click();expect(page.locator('.workspace-main')).not_to_have_attribute('inert','')
    expect(page.get_by_role('button',name='Toggle navigation')).to_be_focused()
    page.get_by_role('button',name='Toggle navigation').click();page.keyboard.press('Escape');expect(page.locator('.nav-backdrop')).not_to_be_visible()
    page.goto(BASE+'/workspace/pipeline/');page.screenshot(path=str(ROOT/'artifacts/mobile-pipeline-refined.png'))
    board=page.locator('.pipeline');assert board.evaluate('(el)=>el.scrollWidth>el.clientWidth')
    board.hover();page.mouse.wheel(600,0);page.wait_for_timeout(300);assert board.evaluate('(el)=>el.scrollLeft')>0
   if width==1440:
    page.goto(BASE+'/workspace/');page.screenshot(path=str(ROOT/'artifacts/desktop-management-refined.png'))
    expect(page.locator('#workspace-nav')).not_to_have_attribute('inert','')
   results.append(f'Management, CRM, record cards, reports and forms fit at {width}px')
  assert not errors,errors
  browser.close()
 (ROOT/'artifacts/responsive-results.json').write_text(json.dumps({'url':BASE,'widths':WIDTHS,'checks':results,'javascript_errors':errors},indent=2)+'\n')
 print(json.dumps(results,indent=2))
if __name__=='__main__':main()
