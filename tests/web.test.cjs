'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');
const source = name => fs.readFileSync(path.join(__dirname, '../web', name), 'utf8');
function launcher() {
  const elements = {};
  for (const name of ['canvas','overlay','status','start','storage','stage','fullscreen']) elements[name] = {addEventListener(){},focus(){},disabled:true};
  const events = {}; let calls=0;
  const ctx = {document:{getElementById:id=>elements[id],baseURI:'https://example.test/sub/'},console,URL,
    setTimeout:()=>1,clearTimeout(){},location:{reload(){}},Love(){calls++;return Promise.resolve();}};
  ctx.window = ctx; ctx.addEventListener = (name,fn) => {events[name]=fn;};
  vm.runInNewContext(source('app.js'),ctx);
  return {ctx,elements,events,calls:()=>calls};
}
test('launch requires a gesture and runs once; assets remain relative', () => {
  const {ctx,elements,calls}=launcher();
  assert.equal(calls(),0); ctx.engineReady(); assert.equal(elements.start.disabled,false);
  elements.start.onclick(); elements.start.onclick(); assert.equal(calls(),1);
  assert.equal(ctx.Module.locateFile('love.wasm'),'https://example.test/sub/love.wasm');
});
test('async errors show recovery and storage failure is nonfatal', () => {
  const {ctx,elements,events}=launcher();
  ctx.Module.onStorageWarning(); assert.match(elements.storage.textContent,/unavailable/);
  events.error({message:'download failed'}); assert.match(elements.status.textContent,/download failed/);
  assert.equal(elements.start.textContent,'Reload'); assert.equal(elements.overlay.hidden,false);
});
function persistence(failHydration=false) {
  const callbacks=[];let released=0;
  const ctx={Module:{addRunDependency(){},removeRunDependency(){released++;},onStorageWarning(){}},FS:{mkdirTree(){},mount(){},syncfs(populate,cb){if(populate)cb(failHydration?Error('denied'):null);else callbacks.push(cb);}},IDBFS:{},setInterval(){},document:{addEventListener(){}},window:{addEventListener(){}},console:{warn(){}}};
  vm.runInNewContext(source('persistence.js'),ctx);
  return {ctx,callbacks,released:()=>released};
}
test('denied storage releases startup and allows session-only play',async()=>{
  const {ctx,released}=persistence(true); assert.equal(released(),1); assert.equal(await ctx.Module.flushSaves(),false);
});
test('flush requested during an active write is queued',async()=>{
  const {ctx,callbacks}=persistence();
  const first=ctx.Module.flushSaves(),second=ctx.Module.flushSaves();
  assert.equal(callbacks.length,1); callbacks.shift()(null); assert.equal(await first,true);
  assert.equal(callbacks.length,1); callbacks.shift()(null); assert.equal(await second,true);
});
