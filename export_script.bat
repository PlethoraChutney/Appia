set date_filename=%DATE:~10,4%-%DATE:~4,2%-%DATE:~7,2%
mkdir "results_%date_filename%"
move *.arw .\results_%date_filename%

python assemble_rename_traces.py .\results_%date_filename%\
set /p descriptive_filename=<temp.txt
ren results_%date_filename% %descriptive_filename%
del temp.txt

copy auto_graph.R .\%descriptive_filename%
cd .\%descriptive_filename%
Rscript .\auto_graph.R --no-save --no-restore
del .\auto_graph.R

exit