@echo off

python appia.py process ./* --database

if %ERRORLEVEL%==1 (
    PAUSE
)