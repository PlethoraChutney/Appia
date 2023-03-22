if (!(Get-Command docker -errorAction SilentlyContinue))
{
    Write-Host "You must install docker: https://www.docker.com/products/docker-desktop/"
    exit 1
}

Write-Host "Downloading files from github"

Move-Item docker-compose.yml old-docker-compose.yml -errorAction SilentlyContinue
Move-Item local.ini old-local-ini -errorAction SilentlyContinue

Invoke-WebRequest https://raw.githubusercontent.com/PlethoraChutney/Appia/main/docker-compose.yml -OutFile docker-compose.yml
Invoke-WebRequest https://raw.githubusercontent.com/PlethoraChutney/Appia/main/local.ini -OutFile local.ini

if (Test-Path .\launch-appia.ps1)
{
    Write-Host Detected old launch-appia.ps1 script.
    .\launch-appia.ps1 nolaunch
}

if (!(Test-Path env:COUCHDB_USER))
{
    $env:COUCHDB_USER = Read-Host "What would you like your CouchDB username to be?"
}
if (!(Test-Path env:COUCHDB_PASSWORD))
{
    $env:COUCHDB_PASSWORD = Read-Host "What would you like your CouchDB password to be?"
}

# here we assume that all windows machines will be x86_64...
$env:APPIA_ARCH = ""

@"
if (!(docker stats --no-stream 2>`$null))
{
    Write-Host Launching docker...
    Start-Process "C:\Program Files\Docker\Docker\Docker Desktop.exe"

    while (!(docker stats --no-stream 2>`$null))
    {
        Write-Host Waiting for docker to start...
        Start-Sleep -Seconds 1
    }
}

`$env:COUCHDB_USER = '$env:COUCHDB_USER'
`$env:COUCHDB_PASSWORD = '$env:COUCHDB_PASSWORD'
`$env:APPIA_ARCH = '$env:APPIA_ARCH'

if (`$args.Count -eq 0)
{
    docker-compose up -d
}
"@ > launch-appia.ps1

Write-Host All set! You can launch Appia Web by running .\launch-appia.ps1