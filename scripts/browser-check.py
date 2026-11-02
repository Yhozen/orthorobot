"""Integration checks against the actual static output; requires Python Playwright + Chromium.
Run with an HTTP server serving the repo: python3 scripts/browser-check.py
Screenshots cover gameplay transitions for visual review; assertions cover storage/audio/network.
"""
import json, os
from pathlib import Path
from playwright.sync_api import sync_playwright
OUT=Path('evidence');OUT.mkdir(exist_ok=True)
URL=os.environ.get('GAME_URL','http://127.0.0.1:8080/dist/')
report={};logs=[]
AUDIO='''window.audioContexts=[];window.analysers=[];const Native=window.AudioContext;
window.AudioContext=class extends Native {constructor(...args){super(...args);window.audioContexts.push(this);}};
const connect=AudioNode.prototype.connect;AudioNode.prototype.connect=function(dest,...args){
if(dest instanceof AudioDestinationNode){const a=this.context.createAnalyser();connect.call(this,a);window.analysers.push(a);}return connect.call(this,dest,...args);};
window.sampleAudio=()=>Math.max(0,...analysers.map(a=>{const d=new Float32Array(a.fftSize);a.getFloatTimeDomainData(d);return Math.max(...d.map(Math.abs));}));'''
READ='''async()=>{const db=await new Promise((resolve,reject)=>{const r=indexedDB.open('/home/web_user/love');r.onsuccess=()=>resolve(r.result);r.onerror=()=>reject(r.error);});
return await new Promise((resolve,reject)=>{const tx=db.transaction('FILE_DATA','readonly');const r=tx.objectStore('FILE_DATA').getAll();r.onsuccess=()=>resolve(r.result.map(v=>v.contents?new TextDecoder().decode(v.contents):''));r.onerror=()=>reject(r.error);tx.oncomplete=()=>db.close();});}'''
with sync_playwright() as p:
 browser=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox','--enable-unsafe-swiftshader'])
 report['browser']=browser.version
 context=browser.new_context(viewport={'width':1100,'height':1100});context.add_init_script(AUDIO)
 page=context.new_page();errors=[];bad=[]
 page.on('console',lambda m:logs.append(m.type+': '+m.text));page.on('pageerror',lambda e:errors.append(str(e)))
 page.on('response',lambda r:bad.append([r.status,r.url]) if r.status>=400 else None)
 def boot():
  page.goto(URL);page.locator('#start').click();page.wait_for_timeout(5000);assert page.locator('#overlay').is_hidden()
 def shot(name):page.screenshot(path=str(OUT/(name+'.png')))
 def click(x,y,wait=1600):page.locator('#canvas').click(position={'x':x,'y':y});page.wait_for_timeout(wait)
 boot();shot('menu')
 peaks=[]
 for _ in range(10):peaks.append(page.evaluate('sampleAudio()'));page.wait_for_timeout(100)
 report['audio']={'contexts':page.evaluate('audioContexts.map(c=>({state:c.state,time:c.currentTime}))'),'peak':max(peaks)}
 assert max(peaks)>0, 'No rendered audio samples'
 click(512,300);shot('levels');click(125,60,4500);shot('level1')
 page.keyboard.press('ArrowRight');page.wait_for_timeout(500);shot('movement')
 box=page.locator('#canvas').bounding_box();page.mouse.move(box['x']+500,box['y']+350);page.mouse.down();page.mouse.move(box['x']+700,box['y']+450,steps=20);page.mouse.up();page.wait_for_timeout(1200);shot('perspective')
 page.keyboard.press('Escape');page.wait_for_timeout(800);shot('pause')
 click(512,387,4500);shot('retry')
 for _ in range(10):page.keyboard.press('ArrowRight');page.wait_for_timeout(250)
 page.wait_for_timeout(2500);shot('completed')
 assert page.evaluate('Module.flushSaves()')
 saved=page.evaluate(READ);report['completedSave']=saved
 assert any('map=01.txt;time=' in s for s in saved), 'Level completion not saved'
 click(512,556,3000);shot('return-menu')
 click(100,12);assert page.evaluate('Module.flushSaves()');saved=page.evaluate(READ)
 assert any('sound=false;' in s for s in saved);report['soundPreferenceSave']=True
 page.reload();page.locator('#start').click();page.wait_for_timeout(5000);shot('reloaded-menu');click(512,300);shot('reloaded-levels');click(370,60,4500);shot('level2-after-reload')
 report['reloadSave']=page.evaluate(READ);assert report['reloadSave']==saved
 report['errors']=errors;report['failedRequests']=bad;assert not errors and not bad
 report['gameplay']='Screenshots captured for menu, levels, movement, perspective, pause, retry, level completion, return, reload and unlocked level 2; visual review required.'
 (OUT/'browser-report.json').write_text(json.dumps(report,indent=2));(OUT/'browser-console.log').write_text('\n'.join(logs))
 context.close()
 denied=browser.new_context(viewport={'width':1100,'height':1100})
 denied.add_init_script("Object.defineProperty(window,'indexedDB',{get(){throw new DOMException('Blocked for test','SecurityError')}})")
 page=denied.new_page();denied_errors=[];page.on('pageerror',lambda e:denied_errors.append(str(e)))
 boot();shot('denied-storage');assert 'unavailable' in page.locator('#storage').inner_text();assert page.evaluate('Module.flushSaves()') is False
 click(512,300);click(125,60,4500);shot('denied-storage-gameplay');assert not denied_errors
 report['deniedStorage']='PASS: menu and level render, startup released, warning shown, flush returns false'
 denied.close();browser.close()
(OUT/'browser-report.json').write_text(json.dumps(report,indent=2));(OUT/'browser-console.log').write_text('\n'.join(logs))
print(json.dumps(report,indent=2))
