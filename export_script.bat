@echo off

python scripts\assemble_rename_traces.py .

IF %ERRORLEVEL%==1 (
  PAUSE
)
