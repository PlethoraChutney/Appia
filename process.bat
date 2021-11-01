@echo off

python appia.py --ignore-gooey process ./* --database

if %ERRORLEVEL%==1 (
    PAUSE
)