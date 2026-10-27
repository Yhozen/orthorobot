"""Real browser storage corruption, loading failure and fullscreen checks."""
import json
from pathlib import Path
from playwright.sync_api import sync_playwright
OUT=Path('evidence');URL='http://127.0.0.1:8080/dist/'
results={}
WRITE='''async text=>{const db=await new Promise((resolve,reject)=>{const r=indexedDB.open('/home/web_user/love');r.onsuccess=()=>resolve(r.result);r.onerror=()=>reject(r.error)});await new Promise((resolve,reject)=>{const tx=db.transaction('FILE_DATA','readwrite');const store=tx.objectStore('FILE_DATA');const keys=store.getAllKeys();keys.onsuccess=()=>{const key=keys.result.find(k=>k.endsWith('/save.txt'));if(!key){reject(Error('No existing save key: '+keys.result));return;}store.put({timestamp:new Date(),mode:33206,contents:new TextEncoder().encode(text)},key);};tx.oncomplete=()=>{db.close();resolve()};tx.onerror=()=>reject(tx.error)});}'''
with sync_playwright() as p:
 b=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox','--enable-unsafe-swiftshader'])
 context=b.new_context(viewport={'width':1100,'height':1100});page=context.new_page();errors=[]
 page.on('pageerror',lambda e:errors.append(str(e)))
 page.goto(URL);page.locator('#start').click();page.wait_for_timeout(5000)
 page.locator('#canvas').click(position={'x':100,'y':12});page.wait_for_timeout(500);assert page.evaluate('Module.flushSaves()')
 # Seed actual IndexedDB records, then let the unchanged game load them on reload.
 page.evaluate(WRITE,'time=bad;map=unknown;coins=1,2;scale=0;sound=oops;map=16.txt;time=3.14;steps=2;warps=0;')
 page.reload();page.locator('#start').click();page.wait_for_timeout(5000);assert page.locator('#overlay').is_hidden()
 page.locator('#canvas').click(position={'x':512,'y':300});page.wait_for_timeout(1500)
 page.screenshot(path=str(OUT/'final-save-unlocks.png'))
 # Last level must be selectable without overflowing currentmap.
 page.locator('#canvas').click(position={'x':870,'y':360});page.wait_for_timeout(5000)
 page.screenshot(path=str(OUT/'level16.png'))
 assert not errors
 results['corruptFinalSave']='Startup passed; verify final-save-unlocks and level16 screenshots for unlock/selection'
 page.locator('#fullscreen').click();page.wait_for_timeout(300)
 results['fullscreen']=page.evaluate('!!document.fullscreenElement');assert results['fullscreen']
 dims=page.locator('#canvas').bounding_box();assert abs(dims['width']/dims['height']-4/3)<0.01
 page.keyboard.press('Escape');context.close()
 for asset in ['love.wasm','game.data','love.js']:
  c=b.new_context();page=c.new_page();page.route('**/'+asset,lambda route:route.abort())
  page.goto(URL)
  if asset!='love.js':page.locator('#start').click()
  page.wait_for_timeout(3000)
  assert page.locator('#overlay').is_visible()
  assert page.locator('#start').inner_text()=='Reload',(asset,page.locator('#status').inner_text())
  results[asset+' failure']=page.locator('#status').inner_text()
  page.screenshot(path=str(OUT/(asset.replace('.','-')+'-failure.png')));c.close()
 b.close()
(OUT/'browser-edge-report.json').write_text(json.dumps(results,indent=2));print(json.dumps(results,indent=2))
