"""Optional browser QA. Uses installed Chrome; Playwright is a development-only tool.
Run against the local seeded dev server: .venv/bin/python tests/browser_smoke.py
"""
import json
from pathlib import Path
from playwright.sync_api import sync_playwright,expect
BASE='http://127.0.0.1:8000'
ROOT=Path(__file__).resolve().parent.parent

def run():
 with sync_playwright() as p:
  browser=p.chromium.launch(executable_path='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',headless=True,args=['--no-first-run'])
  context=browser.new_context(viewport={'width':1440,'height':1000})
  page=context.new_page();errors=[];page.on('pageerror',lambda err:errors.append(str(err)))
  results=[]
  def check_layout(label):
   width=page.evaluate('({viewport:innerWidth,document:document.documentElement.scrollWidth})')
   assert width['document']<=width['viewport'],f'{label} overflow: {width}'
   results.append(label+' has no page overflow')
  page.goto(BASE);expect(page.get_by_role('heading',name='Find Your Next Property. Manage Your Real Estate Smarter.')).to_be_visible()
  page.locator('img').evaluate_all("imgs=>imgs.forEach(img=>img.loading='eager')");page.wait_for_function("Array.from(document.images).every(img=>img.complete && img.naturalWidth>0)");page.screenshot(path=str(ROOT/'artifacts/home-desktop.png'),full_page=True);page.screenshot(path=str(ROOT/'artifacts/home-preview.png'));check_layout('Desktop homepage')
  assert page.locator('img').evaluate_all('(imgs)=>imgs.every(img=>img.complete && img.naturalWidth>0)')
  favorite=page.get_by_role('button',name='Save Ocean-view Villa, Masaki').first;favorite.click();expect(favorite).to_have_attribute('aria-pressed','true');page.reload();expect(favorite).to_have_attribute('aria-pressed','true');favorite.click()
  page.locator('.hero-search select[name=region]').select_option(label='Dar es Salaam')
  page.get_by_role('button',name='Search properties').click();expect(page.get_by_role('heading',name='Find your place in Tanzania.')).to_be_visible()
  assert 'region=Dar+es+Salaam' in page.url
  page.goto(BASE+'/properties/demo-property-01/')
  page.get_by_label('Name:',exact=True).fill('Browser QA Sample')
  page.get_by_label('Phone:',exact=True).fill('+255712345678')
  page.get_by_label('Email (optional)',exact=False).count() # email is optional, label from Django is Email:
  page.get_by_label('Email:',exact=True).fill('browser-qa@example.invalid')
  page.get_by_label('Message:',exact=True).fill('Sample enquiry created by browser verification.')
  page.get_by_label('Request a viewing',exact=False).check()
  page.get_by_role('button',name='Send enquiry').click();expect(page.get_by_text('Enquiry sent.',exact=False)).to_be_visible();results.append('Public enquiry submitted successfully')
  page.goto(BASE+'/accounts/login/')
  page.get_by_label('Username:').fill('demo_agent');page.get_by_label('Password:',exact=True).fill('EstateDemo2026!');page.get_by_role('button',name='Sign in →').click()
  expect(page.get_by_role('heading',name='Portfolio overview')).to_be_visible()
  page.goto(BASE+'/workspace/records/leads/?q=Browser+QA+Sample');page.get_by_role('link',name='Browser QA Sample',exact=True).first.click()
  page.get_by_label('Lead stage').select_option('qualified');page.get_by_role('button',name='Update stage').click();expect(page.get_by_text('Lead stage updated.',exact=True)).to_be_visible();results.append('Enquiry visible to agent; lead stage persisted')
  page.get_by_role('link',name='Schedule viewing',exact=True).click();page.get_by_label('Date:',exact=True).fill('2026-11-10T10:00');page.get_by_label('Status:',exact=True).select_option('confirmed');page.get_by_role('button',name='Save record').click();expect(page.get_by_text('Viewing saved successfully.',exact=True)).to_be_visible();results.append('Agent scheduled a viewing')
  page.goto(BASE+'/workspace/pipeline/');check_layout('Desktop CRM pipeline');page.screenshot(path=str(ROOT/'artifacts/crm-desktop.png'),full_page=True)
  page.get_by_role('button',name='Sign out',exact=False).click();page.goto(BASE+'/accounts/login/');page.get_by_label('Username:').fill('demo_manager');page.get_by_label('Password:',exact=True).fill('EstateDemo2026!');page.get_by_role('button',name='Sign in →').click()
  page.screenshot(path=str(ROOT/'artifacts/management-desktop.png'),full_page=True);check_layout('Desktop management')
  page.goto(BASE+'/workspace/records/properties/new/');page.get_by_label('Name:',exact=True).fill('Browser QA Draft Property');page.get_by_label('Description:',exact=True).fill('Sample property for end-to-end browser verification.');page.get_by_label('Property type:',exact=True).select_option('house');page.get_by_label('Purpose:',exact=True).select_option('rent');page.get_by_label('Location:',exact=True).fill('Masaki');page.get_by_label('Region:',exact=True).fill('Dar es Salaam');page.get_by_label('Price:',exact=True).fill('1500000');page.get_by_label('Size:',exact=True).fill('120');page.get_by_role('button',name='Save record').click();expect(page.get_by_text('Property saved successfully.',exact=True)).to_be_visible();page.get_by_role('button',name='Approve & publish').click();expect(page.get_by_text('Listing published.',exact=True)).to_be_visible();page.get_by_role('link',name='View public listing').click();expect(page.get_by_role('heading',name='Browser QA Draft Property')).to_be_visible();results.append('Manager created, published and opened a new listing')
  page.goto(BASE+'/workspace/records/inspections/new/');page.get_by_label('Property:',exact=True).select_option(index=1);page.get_by_label('Date:',exact=True).fill('2026-11-11T11:00');page.get_by_label('Inspection type:',exact=True).fill('Browser QA draft');context.set_offline(True);page.get_by_role('button',name='Save local draft').click();expect(page.get_by_text('Saved locally on this browser.',exact=False)).to_be_visible();context.set_offline(False);page.reload();page.get_by_role('button',name='Load draft').click();expect(page.get_by_label('Inspection type:',exact=True)).to_have_value('Browser QA draft');page.get_by_role('button',name='Save record').click();expect(page.get_by_text('Inspection draft successfully synchronized.',exact=True)).to_be_visible();page.goto(BASE+'/workspace/records/inspections/new/');expect(page.get_by_text('Successfully synchronized',exact=False)).to_be_visible();page.get_by_role('button',name='Delete',exact=True).click();results.append('Offline draft stored, reloaded and manually synchronized')
  mobile=browser.new_context(viewport={'width':390,'height':844},is_mobile=True,device_scale_factor=1)
  m=mobile.new_page();m.goto(BASE);expect(m.locator('#public-nav')).not_to_be_visible();m.get_by_role('button',name='Menu',exact=False).click();expect(m.locator('#public-nav')).to_be_visible();m.get_by_role('link',name='Properties',exact=True).click();expect(m.get_by_role('heading',name='Find your place in Tanzania.')).to_be_visible()
  for url,label in [('/','Mobile homepage'),('/properties/','Mobile directory'),('/properties/demo-property-01/','Mobile property detail'),('/accounts/login/','Mobile login')]:
   m.goto(BASE+url);size=m.evaluate('({viewport:innerWidth,document:document.documentElement.scrollWidth})');assert size['document']<=size['viewport'],(label,size);results.append(label+' has no page overflow')
  m.goto(BASE);m.locator('img').evaluate_all("imgs=>imgs.forEach(img=>img.loading='eager')");m.wait_for_function("Array.from(document.images).every(img=>img.complete && img.naturalWidth>0)");m.screenshot(path=str(ROOT/'artifacts/home-mobile.png'),full_page=True);m.screenshot(path=str(ROOT/'artifacts/home-mobile-preview.png'))
  m.goto(BASE+'/accounts/login/');m.get_by_label('Username:').fill('demo_manager');m.get_by_label('Password:',exact=True).fill('EstateDemo2026!');m.get_by_role('button',name='Sign in →').click()
  for url,label in [('/workspace/','Mobile management'),('/workspace/pipeline/','Mobile pipeline'),('/workspace/records/properties/','Mobile property table'),('/workspace/records/inspections/new/','Mobile inspection form')]:
   m.goto(BASE+url);size=m.evaluate('({viewport:innerWidth,document:document.documentElement.scrollWidth})');assert size['document']<=size['viewport'],(label,size);results.append(label+' has no page overflow')
  m.goto(BASE+'/workspace/');m.get_by_role('button',name='Toggle navigation').click();expect(m.locator('#workspace-nav')).to_be_visible();m.get_by_role('link',name='Tenants',exact=False).click();expect(m.get_by_role('heading',name='Tenants',exact=True)).to_be_visible();results.append('Mobile public and workspace navigation work')
  assert not errors,errors
  (ROOT/'artifacts/browser-results.json').write_text(json.dumps({'checks':results,'javascript_errors':errors},indent=2));print(json.dumps(results,indent=2))
  browser.close()
if __name__=='__main__':run()
