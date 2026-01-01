function love.conf(t)
	t.title = "Ortho Robot"
	t.identity = "ortho_robot"
	t.author = "Maurice"
	
	-- LÖVE 11.x uses t.window (t.screen is deprecated)
	if t.window then
		t.window.vsync = true
		t.window.width = 1024
		t.window.height = 768
	end
end