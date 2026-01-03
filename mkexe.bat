@echo off
@rem Create .exe file. copy to .scr file

setlocal
set BASEFILENAME=pywinscr

set TARGET_SCR=%BASEFILENAME%.scr
set SOURCE_EXE=%BASEFILENAME%.exe
set SOURCE_PYW=%BASEFILENAME%.pyw

@rem ----------------------------------------
@rem Create .exe file by Nuitka

echo ## Create %SOURCE_EXE%
@echo on

python -m nuitka --enable-plugin=tk-inter --windows-console-mode=disable --include-data-file=".\\res\\*.png=.\\res\\" --follow-imports --onefile %SOURCE_PYW%
@rem python -m nuitka --mingw64 --enable-plugin=tk-inter --windows-console-mode=disable --include-data-file=".\\res\\*.png=.\\res\\" --follow-imports --onefile %SOURCE_PYW%

@echo off
@echo.

@rem ----------------------------------------
@rem Delete old .scr file

if exist "%TARGET_SCR%" (
    echo ## Delete "%TARGET_SCR%"
    del "%TARGET_SCR%"
) else (
    echo ## Not found "%TARGET_SCR%". Skip.
)

@rem ----------------------------------------
@rem Copy .exe file to .scr file

if exist "%SOURCE_EXE%" (
    echo ## copy "%SOURCE_EXE%" to "%TARGET_SCR%"
    copy "%SOURCE_EXE%" "%TARGET_SCR%"
) else (
    echo ## Error : Not found "%SOURCE_EXE%"
)
