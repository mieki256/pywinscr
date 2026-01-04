@echo off
@rem Create .exe file.

setlocal
set BASEFILENAME=pywinscr
set SOURCE_PYW=%BASEFILENAME%.pyw
set SOURCE_EXE=%BASEFILENAME%.exe
set TARGET_SCR=%BASEFILENAME%.scr

echo ----------------------------------------
echo Create %SOURCE_EXE% using Nuitka
@echo on

python -m nuitka --remove-output --enable-plugin=tk-inter --windows-console-mode=disable --include-data-dir="./res=res" --follow-imports --onefile %SOURCE_PYW%

@rem python -m nuitka --mingw64 --remove-output --enable-plugin=tk-inter --windows-console-mode=disable --include-data-dir="./res=res" --follow-imports --onefile %SOURCE_PYW%

