@echo off
REM JuRu one-step setup - installs the interpreter for the current user,
REM the same way Python's per-user install does. No admin rights needed.

setlocal

set "JDIR=%LOCALAPPDATA%\Programs\JuRu"

echo.
echo  JuRu setup - installing to %JDIR%
echo.

if not exist "%JDIR%" mkdir "%JDIR%"
copy /Y "%~dp0juru.exe" "%JDIR%\juru.exe" >nul
if errorlevel 1 (
    echo  setup failed: could not copy juru.exe
    pause
    exit /b 1
)

REM 1. Put juru on the user PATH (open a NEW terminal to see it).
powershell -NoProfile -Command "$d='%JDIR%';$p=[Environment]::GetEnvironmentVariable('Path','User');if(($p -split ';') -notcontains $d){[Environment]::SetEnvironmentVariable('Path',($p.TrimEnd(';')+';'+$d),'User');echo '  PATH: added (open a NEW terminal)'}else{echo '  PATH: already set'}"

REM 2. Give .jr files the JuRu icon and double-click run, like .py files.
reg add "HKCU\Software\Classes\.jr" /ve /d "JuRu.source" /f >nul
reg add "HKCU\Software\Classes\JuRu.source" /ve /d "JuRu source file" /f >nul
reg add "HKCU\Software\Classes\JuRu.source\DefaultIcon" /ve /d "%JDIR%\juru.exe" /f >nul
reg add "HKCU\Software\Classes\JuRu.source\shell\open\command" /ve /d "\"%JDIR%\juru.exe\" \"%%1\" %%*" /f >nul

echo   .jr files: JuRu icon + double-click run  (press F5 in Explorer if
echo              the icon does not show at once)
echo.
echo  done. Open a NEW terminal, then:
echo.
echo     juru --version
echo     juru --new mygame starter
echo     juru mygame.jr
echo.
pause
