"""Read-only public deployment smoke checks; creates no agency/property/customer records."""
import json,os
from pathlib import Path
from playwright.sync_api import sync_playwright,expect
BASE='https://afyasoft.co.tz'
ROOT=Path(__file__).resolve().parent.parent
PREFIX=os.environ.get('ESTATE_QA_ARTIFACT_PREFIX','live')

def main():
 results=[];errors=[]
 with sync_playwright() as p:
  browser=p.chromium.launch(executable_path='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',headless=True)
  context=browser.new_context(viewport={'width':1440,'height':1000})
  page=context.new_page();page.on('pageerror',lambda error:errors.append(str(error)))
  response=page.goto(BASE+'/',wait_until='networkidle');assert response.status==200
  expect(page.get_by_role('heading',name='Find Your Next Property. Manage Your Real Estate Smarter.')).to_be_visible()
  page.locator('img').evaluate_all("imgs=>imgs.forEach(img=>img.loading='eager')")
  page.wait_for_function('Array.from(document.images).every(img=>img.complete&&img.naturalWidth>0)')
  page.screenshot(path=str(ROOT/f'artifacts/{PREFIX}-home-desktop.png'))
  results.append('HTTPS homepage and locally served photographs load')
  for route in ['/properties/','/properties/demo-property-01/','/agents/','/agencies/','/pricing/','/about/','/contact/','/demo/','/accounts/login/','/accounts/register/','/accounts/password_reset/']:
   response=page.goto(BASE+route);assert response.status==200,(route,response.status)
  results.append('All eleven public/account routes return HTTP 200')
  page.goto(BASE+'/properties/?purpose=rent&region=Dar+es+Salaam&property_type=apartment')
  expect(page.locator('select[name=purpose]')).to_have_value('rent');expect(page.locator('select[name=region]')).to_have_value('Dar es Salaam')
  assert page.locator('.property-card').count()>0
  results.append('Live property filters return database listings')
  page.goto(BASE+'/workspace/');assert '/accounts/login/' in page.url
  results.append('Private workspace requires authentication')
  page.get_by_label('Username:').fill('demo_admin');page.get_by_label('Password:',exact=True).fill('EstateDemo2026!');page.get_by_role('button',name='Sign in →').click()
  expect(page.get_by_text('Please enter a correct username and password.',exact=False)).to_be_visible()
  results.append('Public demo password cannot authenticate; HTTPS login CSRF validation works')
  csrf=[c for c in context.cookies() if c['name']=='csrftoken'];assert csrf and csrf[0]['secure'] and csrf[0]['httpOnly']
  results.append('CSRF cookie is Secure and HttpOnly')
  mobile=browser.new_context(viewport={'width':390,'height':844},is_mobile=True,device_scale_factor=1)
  m=mobile.new_page();m.on('pageerror',lambda error:errors.append(str(error)))
  for route in ['/','/properties/','/properties/demo-property-01/','/accounts/register/']:
   m.goto(BASE+route);sizes=m.evaluate('({viewport:innerWidth,document:document.documentElement.scrollWidth})');assert sizes['document']<=sizes['viewport'],(route,sizes)
  results.append('Live mobile homepage, directory, detail and registration have no horizontal overflow')
  m.goto(BASE+'/');m.screenshot(path=str(ROOT/f'artifacts/{PREFIX}-home-mobile.png'));m.get_by_role('button',name='Menu',exact=False).click();expect(m.locator('#public-nav')).to_be_visible();m.get_by_role('link',name='Properties',exact=True).click();expect(m.get_by_role('heading',name='Find your place in Tanzania.')).to_be_visible()
  results.append('Live mobile navigation opens and follows links')
  assert not errors,errors
  browser.close()
 (ROOT/f'artifacts/{PREFIX}-browser-results.json').write_text(json.dumps({'url':BASE,'checks':results,'javascript_errors':errors},indent=2)+'\n')
 print(json.dumps(results,indent=2))
if __name__=='__main__':main()
