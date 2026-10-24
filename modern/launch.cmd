@echo off
setlocal
if exist "%~dp0.tools\w64devkit\bin\gcc.exe" set "PATH=%~dp0.tools\w64devkit\bin;%PATH%"
set "DEVCPP_WORKSPACE=%~dp0examples\hello"
if not "%~1"=="" set "DEVCPP_WORKSPACE=%~1"
if exist "%~dp0dist\DevCppModern\DevCppModern.exe" (
  "%~dp0dist\DevCppModern\DevCppModern.exe" "%DEVCPP_WORKSPACE%"
) else (
  "%~dp0..\.venv\Scripts\python.exe" -m devcpp.app "%DEVCPP_WORKSPACE%"
)
endlocal
