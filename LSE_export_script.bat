@echo off

set /P new_name="Rename experiment to: "

python scripts\assemble_traces.py . --very-large --no-plots --rename "%new_name%"

IF %ERRORLEVEL%==1 (
  PAUSE
)
