# The idea here is that we have a watcher that will notice when Waters writes a
# report to some folder. Then we can use this script to run the assemble_traces
# script to automatically compile the run and add it to the database.

$DOCDIR = [Environment]::GetFolderPath("MyDocuments")
$FOLDER = "$DOCDIR\experiment_watcher\reports"
$TRACES = "$DOCDIR\experiment_watcher\traces"
$FILTER = "*.pdf"
$ASSEMBLE_COM = "python .\assemble_traces.py $TRACES"

$WATCHER = New-Object IO.FileSystemWatcher $FOLDER, $FILTER -Property @{
  IncludeSubdirectories = $false
  NotifyFilter = [IO.NotifyFilters]'FileName, LastWrite'
}

$ON_CREATED = Register-ObjectEvent $WATCHER Created -SourceIdentifier FileCreated -Action {
  Invoke-Expression $ASSEMBLE_COM
}
