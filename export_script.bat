@echo off

python new-web-ui\assemble_traces.py .

IF %ERRORLEVEL%==1 (
  PAUSE
)
