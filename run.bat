setlocal enabledelayedexpansion

for /l %%i in (0, 1, 4) do (
	set /a "x = %%i * 286 - 10"
	for /l %%j in (0, 1, 1) do (
		set /a "y= %%j * 450 - 10"
		start C:\Users\Gregory\AppData\Local\Programs\Python\Python312\pythonw.exe C:\progs\beeg\beeg.py 460 530 !x! !y!
		timeout 1
	)
)


wmic process where "CommandLine LIKE '%%beeg.py%%'" CALL setpriority "idle"
