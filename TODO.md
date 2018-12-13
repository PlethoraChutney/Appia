# Batch script
 - I'd rather not use a batch file at all. This would involve re-writing
 the data-vis stuff into python, or figuring out how to get R to do the data
 manipulation
 - I don't think I need a unix shell script, since I believe Waters instruments
 only run on Windows.

# 2D R script
 - Users should be able to define peaks to normalize the traces against
 - The script should produce 3 additional plots, each normalized to one of the
 three largest peaks.

# Web UI
 - Code needs to be refactored, in general. It's hard to read, since I wrote
 it in a weekend
 - Maybe move it out of its own folder? Annoying to have to go up to the parent
 directory for traces.
 - Right now, there is native R code to process the data. This is all hard-coded
 to my column positions. Perhaps I should have it go up to the parent directory
 and find the correct python script, then run that, since the user has
 configured it.
   - Alternately, I could make a universal config file. Might be easier.
