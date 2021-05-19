@echo off

python3 appia.py -v process ./* --database

if %ERRORLEVEL%==1 (
    PAUSE
)