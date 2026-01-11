@echo off
@rem Create .exe file.

setlocal
set BASEFILENAME=pywinscr
set APPLINAME=PyWinScr
set DESCRIPTION=screensaver
set AUTHORNAME=mieki256
set VERSIONTXT=0.0.1.0
set COMPANYNAME=company

set SOURCE_PYW=%BASEFILENAME%.pyw
set SOURCE_EXE=%BASEFILENAME%.exe
set TARGET_SCR=%BASEFILENAME%.scr

echo ----------------------------------------
echo Create %SOURCE_EXE% using Nuitka
@echo on

python -m nuitka --remove-output --windows-console-mode=disable --include-data-dir="./res=res" --copyright="%AUTHORNAME%" --windows-product-name="%APPLINAME%" --windows-file-description="%DESCRIPTION%" --windows-product-version=%VERSIONTXT% --windows-file-version=%VERSIONTXT% --windows-company-name="%COMPANYNAME%" --follow-imports --onefile %SOURCE_PYW% 

@rem python -m nuitka --mingw64 --remove-output --windows-console-mode=disable --include-data-dir="./res=res" --copyright="%AUTHORNAME%" --windows-product-name="%APPLINAME%" --windows-file-description="%DESCRIPTION%" --windows-product-version=%VERSIONTXT% --windows-file-version=%VERSIONTXT% --windows-company-name="%COMPANYNAME%" --follow-imports --onefile %SOURCE_PYW%

@rem python -m nuitka --remove-output --windows-console-mode=disable --include-data-dir="./res=res" --copyright="%AUTHORNAME%" --windows-product-name="%APPLINAME%" --windows-file-description="%DESCRIPTION%" --windows-product-version=%VERSIONTXT% --windows-file-version=%VERSIONTXT% --windows-company-name="%COMPANYNAME%" --follow-imports --standalone %SOURCE_PYW%
