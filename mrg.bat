@Echo OFF
setlocal EnableDelayedExpansion

FOR /D /R %%# in (*) DO (
	PUSHD "%%#"
	set suffix=1000000
	for /F "delims=" %%i in ('dir /B *.ts') do (
	   set /A suffix+=1
	   ren "%%i" "!suffix:~1!.ts"
	)
	copy /b *ts all.xts
	del *.ts
	move all.xts all.ts
	POPD
)

FOR /D /R %%# in (*) DO (
    PUSHD "%%#"
    FOR %%@ in ("all*") DO (
        Echo Ren: ".\%%~n#\%%@" "%%~n#%%~x@"
        Ren "%%@" "%%~n#%%~x@"
        Move "%%~n#%%~x@" ..
    )
    POPD
)