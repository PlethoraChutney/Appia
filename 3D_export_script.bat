@echo off

set date_filename=results_%DATE:~10,4%-%DATE:~4,2%-%DATE:~7,2%
mkdir %date_filename%
move *.arw .\%date_filename% >nul

for /f "delims=" %%A in ('python 3D_assemble_traces.py .\%date_filename%\') do set "descriptive_filename=%%A"
ren %date_filename% %descriptive_filename% >nul

if exist %descriptive_filename% (
  copy 3D_autograph.R .\%descriptive_filename% >nul
  cd .\%descriptive_filename%
  Rscript .\3D_autograph.R --no-save --no-restore >nul
  del .\3D_autograph.R
) else (
  echo The analyzed trace folder is missing. Exiting without making graphs...
  pause >nul
  exit
)
exit
