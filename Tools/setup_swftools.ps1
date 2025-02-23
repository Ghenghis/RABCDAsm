# PowerShell script to download and setup SWFTools
$swftoolsUrl = "http://www.swftools.org/swftools-2013-04-09-1007.exe"
$installerPath = ".\swftools-installer.exe"

Write-Host "Downloading SWFTools..."
Invoke-WebRequest -Uri $swftoolsUrl -OutFile $installerPath

Write-Host "Installing SWFTools..."
Start-Process -FilePath $installerPath -ArgumentList "/S" -Wait

Write-Host "Adding SWFTools to PATH..."
$env:Path += ";C:\Program Files (x86)\SWFTools"
[Environment]::SetEnvironmentVariable("Path", $env:Path, [System.EnvironmentVariableTarget]::User)

Write-Host "Setup complete!"
