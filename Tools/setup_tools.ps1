# Setup script for dnSpy and Ghidra
$toolsDir = $PSScriptRoot

# URLs for downloads
$dnspyUrl = "https://github.com/dnSpy/dnSpy/releases/download/v6.1.8/dnSpy-net-win64.zip"
$ghidraUrl = "https://github.com/NationalSecurityAgency/ghidra/releases/download/Ghidra_10.3.2_build/ghidra_10.3.2_PUBLIC_20230711.zip"

# Create directories
$dnspyDir = Join-Path $toolsDir "dnspy64"
$ghidraDir = Join-Path $toolsDir "ghidra"

if (-not (Test-Path $dnspyDir)) {
    New-Item -ItemType Directory -Path $dnspyDir | Out-Null
}
if (-not (Test-Path $ghidraDir)) {
    New-Item -ItemType Directory -Path $ghidraDir | Out-Null
}

# Download and extract dnSpy
Write-Host "Downloading dnSpy..."
$dnspyZip = Join-Path $toolsDir "dnspy.zip"
Invoke-WebRequest -Uri $dnspyUrl -OutFile $dnspyZip
Write-Host "Extracting dnSpy..."
Expand-Archive -Path $dnspyZip -DestinationPath $dnspyDir -Force
Remove-Item $dnspyZip

# Download and extract Ghidra
Write-Host "Downloading Ghidra..."
$ghidraZip = Join-Path $toolsDir "ghidra.zip"
Invoke-WebRequest -Uri $ghidraUrl -OutFile $ghidraZip
Write-Host "Extracting Ghidra..."
Expand-Archive -Path $ghidraZip -DestinationPath $ghidraDir -Force
Remove-Item $ghidraZip

# Create batch files for easy launching
$dnspyBat = @"
@echo off
start "" "$dnspyDir\dnSpy.exe" %*
"@
Set-Content -Path (Join-Path $toolsDir "launch_dnspy.bat") -Value $dnspyBat

$ghidraBat = @"
@echo off
start "" "$ghidraDir\ghidra_10.3.2_PUBLIC\ghidraRun.bat" %*
"@
Set-Content -Path (Join-Path $toolsDir "launch_ghidra.bat") -Value $ghidraBat

Write-Host "Setup complete! Use launch_dnspy.bat and launch_ghidra.bat to start the tools."
