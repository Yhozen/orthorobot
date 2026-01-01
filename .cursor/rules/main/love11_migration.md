# LÖVE 11.5 Migration Guide

This document describes the migration process from LÖVE 0.9.x/0.10.x to LÖVE 11.5, based on the successful migration of the Ortho Robot game.

## Overview

LÖVE 11.x introduced breaking changes, most notably:
- **Color values changed from 0-255 range to 0-1 range** for all graphics functions
- **Callback signatures changed** (new parameters added)
- **Audio source creation requires type specification**
- **ImageData:getPixel() returns 0-1 range instead of 0-255**

## Migration Strategy: Color Compatibility Shim

### The Problem
Converting every color value in a codebase (potentially 100+ instances) is error-prone and time-consuming. Additionally, internal game logic often relies on 0-255 values for calculations.

### The Solution
Implement a **global color compatibility shim** that automatically converts 0-255 values to 0-1 range at the API boundary, while keeping internal game logic in 0-255 range.

### Implementation

```lua
--LÖVE 11.5 compatibility shims
local original_setColor = love.graphics.setColor
local original_setBackgroundColor = love.graphics.setBackgroundColor

-- Helper function to convert color values from 0-255 to 0-1 range
local function convertColor(val)
	if type(val) == "number" and val > 1 then
		return val / 255
	end
	return val
end

love.graphics.setColor = function(...)
	local args = {...}
	local n = #args
	-- Handle table argument: setColor({r, g, b, a})
	if n == 1 and type(args[1]) == "table" then
		local t = {}
		for i = 1, math.min(#args[1], 4) do
			t[i] = convertColor(args[1][i])
		end
		return original_setColor(unpack(t))
	end
	-- Handle individual arguments: setColor(r, g, b, a)
	for i = 1, math.min(n, 4) do
		args[i] = convertColor(args[i])
	end
	return original_setColor(unpack(args))
end

love.graphics.setBackgroundColor = function(...)
	local args = {...}
	local n = #args
	-- Handle table argument: setBackgroundColor({r, g, b})
	if n == 1 and type(args[1]) == "table" then
		local t = {}
		for i = 1, math.min(#args[1], 4) do
			t[i] = convertColor(args[1][i])
		end
		return original_setBackgroundColor(unpack(t))
	end
	-- Handle individual arguments: setBackgroundColor(r, g, b)
	for i = 1, math.min(n, 4) do
		args[i] = convertColor(args[i])
	end
	return original_setBackgroundColor(unpack(args))
end
```

### Why This Approach Works

1. **Minimal Code Changes**: Only need to add the shim at the top of `main.lua`
2. **Preserves Game Logic**: Internal calculations remain in 0-255 range
3. **Handles Both Formats**: Works with both table arguments `{r, g, b}` and individual arguments `r, g, b`
4. **Safe Conversion**: Only converts values > 1, so values already in 0-1 range pass through unchanged
5. **Future-Proof**: Easy to remove later if you want to fully migrate to 0-1 range

## Required Changes

### 1. Callback Signatures

Update LÖVE callback functions to match 11.x signatures:

**Before (0.10.x):**
```lua
function love.keypressed(key, unicode)
function love.mousepressed(x, y, button)
function love.mousereleased(x, y, button)
```

**After (11.x):**
```lua
function love.keypressed(key, scancode, isrepeat)
function love.mousepressed(x, y, button, istouch, presses)
function love.mousereleased(x, y, button, istouch, presses)
```

**Note**: You can ignore the new parameters if you don't need them. The old code will still work, but you must update the function signature.

### 2. Audio Source Creation

**Before (0.10.x):**
```lua
sound = love.audio.newSource("sound.ogg")
```

**After (11.x):**
```lua
sound = love.audio.newSource("sound.ogg", "static")  -- for short sound effects
music = love.audio.newSource("music.ogg", "stream")  -- for music/looping audio
```

**Types:**
- `"static"`: Loads entire file into memory. Use for short sound effects. Lower latency.
- `"stream"`: Streams from disk. Use for music or long audio files. Lower memory usage.

### 3. ImageData:getPixel() Return Values

**Critical Change**: `ImageData:getPixel()` now returns values in **0-1 range** instead of 0-255.

**Before (0.10.x):**
```lua
local r, g, b, a = imgdata:getPixel(x, y)
-- r, g, b are 0-255
if r == 255 and g == 0 and b == 0 then
    -- red pixel
end
```

**After (11.x):**
```lua
local r, g, b, a = imgdata:getPixel(x, y)
-- r, g, b are 0-1, need to convert for comparison
r, g, b = round(r*255), round(g*255), round(b*255)
if r == 255 and g == 0 and b == 0 then
    -- red pixel
end
```

**Important**: If your game uses pixel colors for map loading or game logic, you MUST convert the values before comparison.

### 4. Configuration File (conf.lua)

**Before (0.10.x):**
```lua
function love.conf(t)
    if t.screen then
        t.screen.width = 800
        t.screen.height = 600
    end
    if t.window then
        t.window.width = 800
        t.window.height = 600
    end
end
```

**After (11.x):**
```lua
function love.conf(t)
    -- t.screen is deprecated, use t.window only
    if t.window then
        t.window.width = 800
        t.window.height = 600
    end
end
```

### 5. Window Management

**Before (0.10.x):**
```lua
if love.graphics.setMode then
    love.graphics.setMode(width, height, fullscreen, vsync)
elseif love.window.setMode then
    love.window.setMode(width, height, {fullscreen=fullscreen, vsync=vsync})
end
```

**After (11.x):**
```lua
-- Only love.window.setMode exists
love.window.setMode(width, height, {fullscreen=false, vsync=true})
```

## Migration Checklist

- [ ] Add color compatibility shims to `main.lua`
- [ ] Update callback signatures (`love.keypressed`, `love.mousepressed`, `love.mousereleased`)
- [ ] Update all `love.audio.newSource()` calls to include source type
- [ ] Fix `ImageData:getPixel()` usage - convert 0-1 to 0-255 for comparisons
- [ ] Remove deprecated `t.screen` from `conf.lua`
- [ ] Update window management code (remove `love.graphics.setMode` checks)
- [ ] Remove old version compatibility code (0.9.x checks)
- [ ] Test map loading (if using pixel-based maps)
- [ ] Test all game states and transitions
- [ ] Verify colors render correctly
- [ ] Test audio playback

## Common Pitfalls

### 1. ImageData:getPixel() Comparisons
**Problem**: Forgetting to convert 0-1 values to 0-255 before comparing with color tables.

**Solution**: Always convert immediately after `getPixel()`:
```lua
local r, g, b, a = imgdata:getPixel(x, y)
r, g, b = round(r*255), round(g*255), round(b*255)
```

### 2. Color Calculations Breaking
**Problem**: Mixing 0-1 and 0-255 ranges in calculations.

**Solution**: Keep internal game logic in 0-255 range. The shim handles conversion at the API boundary.

### 3. Table Arguments Not Working
**Problem**: Passing tables to `setColor()` doesn't work with the shim.

**Solution**: The shim handles both table and individual arguments. Make sure you're creating a new table in the shim (don't modify the original).

### 4. Background Color Fading
**Problem**: Background color fading uses values that might be interpreted as 0-1.

**Solution**: Keep background colors in 0-255 range internally. The shim converts them when passed to `setBackgroundColor()`.

## Testing

After migration, verify:
1. Game loads without errors
2. Colors display correctly (not too dark/bright)
3. Map loading works (if pixel-based)
4. Audio plays correctly
5. All game states function properly
6. Input handling works (keyboard, mouse)

## Additional Resources

### Official Documentation
- **LÖVE 11.x Wiki**: https://love2d.org/wiki/Main_Page
- **Migration Guide**: https://love2d.org/wiki/11.0
- **Breaking Changes**: https://love2d.org/wiki/11.0#Breaking_Changes

### Key API Changes
- **love.graphics.setColor**: https://love2d.org/wiki/love.graphics.setColor
- **love.audio.newSource**: https://love2d.org/wiki/love.audio.newSource
- **ImageData:getPixel**: https://love2d.org/wiki/ImageData:getPixel

### Version Compatibility
- LÖVE 0.9.x: Uses 0-255 color range
- LÖVE 0.10.x: Uses 0-255 color range
- LÖVE 11.x: Uses 0-1 color range

## Migration Philosophy

**Key Principle**: Minimize code changes while maintaining compatibility.

The color shim approach allows you to:
- Keep existing game logic intact
- Avoid manual conversion of 100+ color calls
- Maintain readability (0-255 is more intuitive for many developers)
- Easily remove the shim later if desired

This approach prioritizes **pragmatism over purity** - it's better to have a working game with a compatibility layer than to risk breaking game logic during a full conversion.

## Future Considerations

If you want to fully migrate to 0-1 range later:
1. Remove the color shim
2. Convert all color tables to 0-1 range
3. Update all color calculations
4. Convert `ImageData:getPixel()` values to 0-1 range
5. Update background color fading logic

However, for most projects, the shim approach is sufficient and less error-prone.

