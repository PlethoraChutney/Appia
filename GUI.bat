@echo off

python appia.py

if %ERRORLEVEL%==1 (
    PAUSE
)