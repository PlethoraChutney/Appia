echo 'Updating scripts from Script_repos'
$userDirectories = 'Rich_Results', 'Arpita_Results', 'Sigrid_Results'
foreach($labmember in $userDirectories)
  {
    Write-Output 'Updating $labmember'
    Copy-Item -path Script_repos\HPLC_Scripts\*.py -destination $labmember -recurse -force -PassThru
    Copy-Item -path Script_repos\HPLC_Scripts\*.R -destination $labmember -recurse -force -PassThru
    Copy-Item -path Script_repos\HPLC_Scripts\*.bat -destination $labmember -recurse -force -PassThru
    Copy-Item -path Script_repos\HPLC_Scripts\*.command -destination $labmember -recurse -force -PassThru
    Copy-Item -path Script_repos\HPLC_Scripts\web_ui -destination $labmember -recurse -force -PassThru
    Copy-Item -path Script_repos\HPLC_Scripts\scripts -destination $labmember -recurse -force -PassThru
  }
write-host "Files copied."
[void][System.Console]::ReadKey($true)
