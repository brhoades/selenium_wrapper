@echo off
set PATH=%PATH%;%~dp0\python27;%~dp0\python27\phantomjs-1.9.7-windows

"%~dp0\python27\python.exe" "%~dp0\run_test.py"

pause
