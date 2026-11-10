@echo off
setlocal
title RealGas Simulator - Setup and Launch
cd /d "%~dp0"
if not exist "run.py" goto missing_files
echo RealGas Simulator - preparing your website...
echo First setup needs Internet. Please keep this window open.
echo.
py -3.12 -c "import sys;sys.exit(sys.version_info < (3,11))" >nul 2>&1
if not errorlevel 1 goto python312
py -3.11 -c "import sys;sys.exit(sys.version_info < (3,11))" >nul 2>&1
if not errorlevel 1 goto python311
py -3 -c "import sys;sys.exit(sys.version_info < (3,11))" >nul 2>&1
if not errorlevel 1 goto pythonlauncher
python -c "import sys;sys.exit(sys.version_info < (3,11))" >nul 2>&1
if not errorlevel 1 goto pythoncommand
python3 -c "import sys;sys.exit(sys.version_info < (3,11))" >nul 2>&1
if not errorlevel 1 goto python3command
echo Python 3.11 or newer was not found. > "setup_log.txt"
echo Install Python 3.12 and tick Add Python to PATH. >> "setup_log.txt"
echo Then run START_WINDOWS.bat again. >> "setup_log.txt"
goto failed
:python312
py -3.12 -u run.py
goto finished
:python311
py -3.11 -u run.py
goto finished
:pythonlauncher
py -3 -u run.py
goto finished
:pythoncommand
python -u run.py
goto finished
:python3command
python3 -u run.py
goto finished
:missing_files
echo Extract the COMPLETE ZIP into a normal folder first.
goto keepopen
:finished
if errorlevel 1 goto failed
goto keepopen
:failed
echo.
echo SETUP COULD NOT FINISH. The error is saved in setup_log.txt.
echo.
if exist "setup_log.txt" type "setup_log.txt"
echo.
echo For immediate use without setup, open OPEN_WEBSITE.html.
echo If you need help, send the contents of setup_log.txt.
:keepopen
echo.
echo This window will remain open. Close it with X or type exit.
cmd /k
