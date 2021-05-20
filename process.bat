@echo off

python appia.py -v process ./* --database

if %ERRORLEVEL%==1 (
    PAUSE
)