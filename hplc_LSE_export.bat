@echo off

set /P new_name="Rename experiment to: "

python appia.py hplc . --reduce 10 --no-plots --rename "%new_name%"

IF %ERRORLEVEL%==1 (
  PAUSE
)
