@echo off

appia process ./* --database

if not %ERRORLEVEL% lss 1 (
    PAUSE
)