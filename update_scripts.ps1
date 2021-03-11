echo 'Updating scripts from Script_repos'
$userDirectories = 'Rich_Results', 'Arpita_HPLC', 'Alex_Results', 'James_Results', 'Kim_Results'
foreach($labmember in $userDirectories)
  {
    Write-Output "Updating $labmember"
    Copy-Item -path Appia\*.py -destination $labmember -recurse -force -PassThru
    Copy-Item -path Appia\*.R -destination $labmember -recurse -force -PassThru
    Copy-Item -path Appia\*.bat -destination $labmember -recurse -force -PassThru
    Copy-Item -path Appia\result_monitor.ps1 -destination $labmember -recurse -force -PassThru
    Copy-Item -path Appia\subcommands -destination $labmember -recurse -force -PassThru
  }
write-host "Files copied."
[void][System.Console]::ReadKey($true)
