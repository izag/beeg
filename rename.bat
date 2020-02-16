@Echo OFF

FOR /D /R %%# in (*) DO (
    PUSHD "%%#"
    FOR %%@ in ("all*") DO (
        Echo Ren: ".\%%~n#\%%@" "%%~n#%%~x@"
        Ren "%%@" "%%~n#%%~x@"
        Move "%%~n#%%~x@" ..
    )
    POPD
)