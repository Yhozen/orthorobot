local contents, written
love = {graphics={setColor=function() end,setBackgroundColor=function() end}, filesystem={}}
love.filesystem.getInfo = function() return contents ~= nil end
love.filesystem.read = function() return contents end
love.filesystem.write = function(_, data) written = data; return true end
dofile('main.lua')
local function reset(data)
 contents=data; filetable={}; for i=1,16 do filetable[i]={path=string.format('%02d.txt',i),collectedcoins={}} end
 scale=1; soundenabled=true; unlockedlevels=1
 loadsave()
end
reset(nil); assert(unlockedlevels==1)
reset('time=oops;map=unknown;time=1;coins=1,2,3;scale=no;sound=what;')
assert(scale==1 and soundenabled and unlockedlevels==1)
reset('map=01.txt;time=1.234;steps=2;warps=0;coins=1,2,3:bad:1.1,2,3;scale=0.75;sound=false;')
assert(filetable[1].hightime==1.23 and filetable[1].highsteps==2 and filetable[1].highwarps==0)
assert(#filetable[1].collectedcoins==1 and scale==0.75 and not soundenabled and unlockedlevels==2)
savesave(); reset(written); assert(filetable[1].hightime==1.23 and #filetable[1].collectedcoins==1)
reset('map=01.txt;time=5;map=unknown;time=1;steps=3;')
assert(filetable[1].hightime==5 and filetable[1].highsteps==nil)
reset('map=16.txt;time=10;map=01.txt;time=20;')
assert(unlockedlevels==16)
reset('map=01.txt;time=nan;steps=-1;warps=inf;scale=0;coins=1,2,3,4;')
assert(filetable[1].hightime==nil and filetable[1].highsteps==nil and filetable[1].highwarps==nil and #filetable[1].collectedcoins==0 and scale==1)
for _,path in ipairs({'main.lua','menu.lua','game.lua'}) do assert(loadfile(path)) end
print('PASS: save defaults, round-trip, corrupt records, unknown maps, preferences, final-level clamp; Lua syntax')
