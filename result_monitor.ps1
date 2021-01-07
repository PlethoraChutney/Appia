# Set folder to watch
$watcher = New-Object System.IO.FileSystemWatcher
$watcher.Path = "C:\Users\HPLC\Documents\Reports"
$watcher.Filter = "*.*"
$watcher.IncludeSubdirectories = $false
$watcher.EnableRaisingevents = $true

# Define action
$action = {
  $path = $Event.SourceEventArgs.FullPath
  if ( $path -Match 'rich' ) {
    C:\Users\HPLC\AppData\Local\Programs\Python\Python38\python.exe C:\Users\HPLC\Documents\Appia\appia.py hplc C:\Users\HPLC\Documents\Rich_Results
  } elseif ( $path -Match 'arpita' ) {
    C:\Users\HPLC\AppData\Local\Programs\Python\Python38\python.exe C:\Users\HPLC\Documents\Appia\appia.py hplc C:\Users\HPLC\Documents\Arpita_Results
  } elseif ( $path -Match 'alex' ) {
    C:\Users\HPLC\AppData\Local\Programs\Python\Python38\python.exe C:\Users\HPLC\Documents\Appia\appia.py hplc C:\Users\HPLC\Documents\Alex_Results
  } elseif ( $path -Match 'james' ) {
    C:\Users\HPLC\AppData\Local\Programs\Python\Python38\python.exe C:\Users\HPLC\Documents\Appia\appia.py hplc C:\Users\HPLC\Documents\James_Results
  } elseif ( $path -Match 'kim' ) {
    C:\Users\HPLC\AppData\Local\Programs\Python\Python38\python.exe C:\Users\HPLC\Documents\Appia\appia.py hplc C:\Users\HPLC\Documents\Kim_Results
  }
}

# Which actions should be watched
Register-ObjectEvent $watcher "Created" -Action $action
while ($true) {sleep 5}
