@echo off

set PATH=%PATH%;%~dp0\python277;%~dp0\python277\phantomjs-1.9.7-windows
set child=3
set times=1

echo You may press enter to use the default values in parenthesis.

set /p child=Number of Children (%child%): 
set /p times=Number of Order Attempts Each (%times%): 
python.exe "%~dp0\run_test.py" "%times%" "%child%"

pause