@echo off

set child=3
set times=3
set staggered=n

set PATH=%PATH%;%~dp0\python27;%~dp0\python27\phantomjs-1.9.7-windows
echo You may press enter to use the default values in parenthesis.

set /p child=Number of Children (%child%): 
set /p times=Number of Jobs to Run (%times%): 
set /p staggered=Stagger Children Spawning (%staggered%): 

"%~dp0\python27\python.exe" "%~dp0\run_test.py" "%times%" "%child%" "%staggered%"

pause
