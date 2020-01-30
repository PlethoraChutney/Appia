@echo off

python appia.py hplc .

IF %ERRORLEVEL%==1 (
  PAUSE
)
