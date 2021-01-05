# Set folder to watch
$watcher = New-Object System.IO.FileSystemWatcher
$watcher.Path = "C:\Users\Rich\Desktop"
$watcher.Filter = "*.*"
$watcher.IncludeSubdirectories = $false
$watcher.EnableRaisingevents = $true

# Define action
$action = {
  $path = $Event.SourceEventArgs.FullPath
  if ( $path -Match "New" )
    {
    D:\Rich\Documents\Scripts\plotly_env/Scripts\python.exe D:\Rich\Documents\Scripts\Appia\appia.py hplc D:\Rich\Documents\Scripts\Appia\HPLC-tests\
    }
}

# Which actions should be watched
Register-ObjectEvent $watcher "Created" -Action $action
while ($true) {sleep 5}
