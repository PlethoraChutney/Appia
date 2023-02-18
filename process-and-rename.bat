@echo off

set /P new_name="Rename experiment to: "

appia process ./* --id "%new_name%" --output-dir "%new_name%" --database

if not %ERRORLEVEL% lss 1 (
    PAUSE
)