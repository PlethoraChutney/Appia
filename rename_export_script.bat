@echo off

set /P new_name="Rename experiment to: "

python appia.py hplc . --rename "%new_name%"

IF %ERRORLEVEL%==1 (
  PAUSE
)
