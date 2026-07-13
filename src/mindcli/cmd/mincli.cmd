@echo off
setlocal
set "DIR=%~dp0"
set "APP_DIR=%DIR%.."
"%APP_DIR%\MindCLI.exe" %*
endlocal
