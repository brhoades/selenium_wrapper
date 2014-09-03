@echo off

set PATH=%PATH%;%~dp0\python277;%~dp0\python277\phantomjs-1.9.7-windows
start "" "%~dp0\includes\conemu\ConEmu64.exe" -cmd "%~dp0\includes\run.bat"