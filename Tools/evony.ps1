# PowerShell Script to Find and Download SWF Files from cc2.evony.com
# Author: AI-Generated
# Run this script using: PowerShell -ExecutionPolicy Bypass -File find_download_swf.ps1

# Set the target domain
$domain = "https://cc2.evony.com"

# Create a folder to store downloaded SWF files
$swfFolder = "$PSScriptRoot\Downloaded_SWF"
if (!(Test-Path -Path $swfFolder)) { New-Item -ItemType Directory -Path $swfFolder }

Write-Host "Starting SWF File Search on $domain`n"

# 1️⃣ Try common SWF filenames
$commonFiles = @("game.swf", "loader.swf", "main.swf", "play.swf", "evony.swf", "flash.swf")

foreach ($file in $commonFiles) {
    $url = "$domain/$file"
    $outputPath = "$swfFolder\$file"

    try {
        Invoke-WebRequest -Uri $url -OutFile $outputPath -ErrorAction Stop
        Write-Host "[✔] Found & Downloaded: $file"
    } catch {
        Write-Host "[✖] Not Found: $file"
    }
}

# 2️⃣ Crawl the main page for any .swf links
Write-Host "`n[🔍] Crawling $domain for SWF links..."
$homepage = Invoke-WebRequest -Uri $domain
$swfLinks = $homepage.Links | Where-Object { $_.href -match "\.swf$" }

foreach ($link in $swfLinks) {
    $swfUrl = "$domain/$($link.href)"
    $swfName = [System.IO.Path]::GetFileName($swfUrl)
    $outputPath = "$swfFolder\$swfName"

    try {
        Invoke-WebRequest -Uri $swfUrl -OutFile $outputPath -ErrorAction Stop
        Write-Host "[✔] Discovered & Downloaded: $swfName"
    } catch {
        Write-Host "[✖] Failed to Download: $swfName"
    }
}

# 3️⃣ Brute-force with additional wordlist
Write-Host "`n[💣] Running Brute Force Search for SWF files..."
$wordlist = @("client.swf", "map.swf", "world.swf", "assets.swf", "interface.swf", "sound.swf", "battle.swf")

foreach ($file in $wordlist) {
    $url = "$domain/$file"
    $outputPath = "$swfFolder\$file"

    try {
        Invoke-WebRequest -Uri $url -OutFile $outputPath -ErrorAction Stop
        Write-Host "[✔] Brute Forced & Downloaded: $file"
    } catch {
        Write-Host "[✖] Not Found: $file"
    }
}

Write-Host "`n[✅] SWF Download Process Completed! Files saved in: $swfFolder"
