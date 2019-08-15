@echo off

python scripts\assemble_traces.py .

IF %ERRORLEVEL%==1 (
  PAUSE
)
