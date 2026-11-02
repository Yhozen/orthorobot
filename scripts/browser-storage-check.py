"""Real-game regression: tab ownership, persisted level completion and lock fallback."""
import json
import os
import shutil
from pathlib import Path
from playwright.sync_api import sync_playwright

URL = os.environ.get('GAME_URL', 'http://127.0.0.1:8080/dist/')
OUT = Path('evidence')
OUT.mkdir(exist_ok=True)
READ = '''async () => {
 const db = await new Promise((resolve, reject) => {
  const r = indexedDB.open('/home/web_user/love');
  r.onsuccess = () => resolve(r.result); r.onerror = () => reject(r.error);
 });
 return await new Promise((resolve, reject) => {
  const tx = db.transaction('FILE_DATA', 'readonly'), result = {};
  const r = tx.objectStore('FILE_DATA').openCursor();
  r.onsuccess = () => {
   const cursor = r.result;
   if (cursor) {
    if (cursor.value.contents) result[cursor.key] = new TextDecoder().decode(cursor.value.contents);
    cursor.continue();
   }
  };
  tx.oncomplete = () => { db.close(); resolve(result); };
  tx.onerror = () => reject(tx.error);
 });
}'''

with sync_playwright() as p:
    browser = p.chromium.launch(
        executable_path=os.environ.get('CHROMIUM') or shutil.which('chromium') or shutil.which('google-chrome'),
        headless=True, args=['--no-sandbox', '--enable-unsafe-swiftshader'])
    context = browser.new_context(viewport={'width': 1100, 'height': 1100})
    errors = []

    def start():
        page = context.new_page()
        page.on('pageerror', lambda error: errors.append(str(error)))
        page.goto(URL)
        page.locator('#start').click()
        return page

    owner = start()
    owner.wait_for_function('document.getElementById("overlay").hidden')
    owner.wait_for_timeout(4500)
    waiting = start()
    waiting.wait_for_function('document.getElementById("status").textContent.includes("another tab")')
    assert waiting.locator('#overlay').is_visible()
    assert waiting.evaluate('Module.flushSaves()') is False
    owner.bring_to_front()
    owner.locator('#canvas').click(position={'x': 512, 'y': 300})
    owner.wait_for_timeout(1500)
    owner.locator('#canvas').click(position={'x': 125, 'y': 60})
    owner.wait_for_timeout(4500)
    for _ in range(10):
        owner.keyboard.press('ArrowRight')
        owner.wait_for_timeout(250)
    owner.wait_for_timeout(2000)
    assert owner.evaluate('Module.flushSaves()')
    saved = owner.evaluate(READ)
    assert any('map=01.txt;time=' in value for value in saved.values()), saved
    owner.close()
    waiting.bring_to_front()
    waiting.wait_for_function('document.getElementById("overlay").hidden')
    waiting.wait_for_timeout(4500)
    assert waiting.evaluate('Module.flushSaves()')
    assert waiting.evaluate(READ) == saved
    waiting.locator('#canvas').click(position={'x': 512, 'y': 300})
    waiting.wait_for_timeout(1500)
    waiting.locator('#canvas').click(position={'x': 370, 'y': 60})
    waiting.wait_for_timeout(4500)
    waiting.screenshot(path=str(OUT / 'storage-handoff-level2.png'))
    assert waiting.evaluate(READ) == saved

    fallback = browser.new_context(viewport={'width': 1100, 'height': 1100})
    fallback.add_init_script("Object.defineProperty(navigator, 'locks', {value: undefined})")
    page = fallback.new_page()
    page.on('pageerror', lambda error: errors.append(str(error)))
    page.goto(URL)
    page.locator('#start').click()
    page.wait_for_function('document.getElementById("overlay").hidden')
    assert 'unavailable' in page.locator('#storage').inner_text()
    assert page.evaluate('Module.flushSaves()') is False
    assert not errors, errors
    report = {'url': URL, 'saveAfterHandoff': saved, 'errors': errors,
              'result': 'PASS: second tab waits, loads persisted completion, keeps level 2 unlocked; missing Web Locks allow session-only play'}
    (OUT / 'browser-storage-report.json').write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))
    browser.close()
