@echo off
@rem Copy .exe to .scr

setlocal
set BASEFILENAME=pywinscr
set SOURCE_PYW=%BASEFILENAME%.pyw
set SOURCE_EXE=%BASEFILENAME%.exe
set TARGET_SCR=%BASEFILENAME%.scr

if exist "%TARGET_SCR%" (
    echo Delete "%TARGET_SCR%"
    del "%TARGET_SCR%"
) else (
    echo Skip. Not found "%TARGET_SCR%".
)

if exist "%SOURCE_EXE%" (
    echo Copy "%SOURCE_EXE%" to "%TARGET_SCR%"
    copy "%SOURCE_EXE%" "%TARGET_SCR%"
) else (
    echo Error : Not found "%SOURCE_EXE%"
)
