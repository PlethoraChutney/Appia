@echo off

set /P new_name="Rename experiment to: "

python appia.py -v process ./* --rename "%new_name%" --database

if %ERRORLEVEL%==1 (
    PAUSE
)