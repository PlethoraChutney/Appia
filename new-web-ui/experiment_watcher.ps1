# The idea here is that we have a watcher that will notice when Waters writes a
# report to some folder. Then we can use this script to run the assemble_traces
# script to automatically compile the run and add it to the database.

$FOLDER = "C:\Users\rich\Desktop\watcher_test"
$FILTER = "*.txt"

$WATCHER = New-Object IO.FileSystemWatcher $FOLDER, $FILTER -Property @{
  IncludeSubdirectories = $false
  NotifyFilter = [IO.NotifyFilters]'FileName, LastWrite'
}

$ON_CREATED = Register-ObjectEvent $WATCHER Created -SourceIdentifier FileCreated -Action {
  $PATH = $Event.SourceEventArgs.FullPath
  $NAME = $Event.SourceEventArgs.Name
  $CHANGE_TYPE = $Event.SourceEventArgs.ChangeType
  $TIME_STAMP = $Event.TimeGenerated
  Write-Host "The file '$NAME' was $CHANGE_TYPE at $TIME_STAMP"
  Write-Host $PATH
}
