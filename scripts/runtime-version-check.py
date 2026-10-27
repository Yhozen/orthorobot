"""Query the shipped engine using a tiny in-memory .love diagnostic, without changing dist."""
import io,zipfile,re,json
from pathlib import Path
from playwright.sync_api import sync_playwright
buf=io.BytesIO()
with zipfile.ZipFile(buf,'w') as z:
 z.writestr('main.lua','function love.load() print("RUNTIME_VERSION", love.getVersion()) end\nfunction love.draw() end')
data=buf.getvalue();loader=Path('dist/game.js').read_text()
loader=re.sub(r'"remote_package_size":\d+',f'"remote_package_size":{len(data)}',loader)
loader=re.sub(r'"end":\d+',f'"end":{len(data)}',loader)
loader=re.sub(r'"package_uuid":"[^"]+"','"package_uuid":"runtime-version-probe"',loader)
with sync_playwright() as p:
 b=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox','--enable-unsafe-swiftshader'])
 page=b.new_page();logs=[];page.on('console',lambda m:logs.append(m.text))
 page.route('**/game.data',lambda r:r.fulfill(body=data,content_type='application/octet-stream'))
 page.route('**/game.js',lambda r:r.fulfill(body=loader,content_type='application/javascript'))
 page.goto('http://127.0.0.1:8080/dist/');page.locator('#start').click();page.wait_for_timeout(3000)
 version=[x for x in logs if 'RUNTIME_VERSION' in x];assert version,logs
 Path('evidence/runtime-version.log').write_text('\n'.join(version));print(version);b.close()
