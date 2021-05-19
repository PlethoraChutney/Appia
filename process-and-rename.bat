@echo off

set /P new_name="Rename experiment to: "

python3 appia.py -v process ./* --rename --database

if %ERRORLEVEL%==1 (
    PAUSE
)