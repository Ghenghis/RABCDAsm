# Setup script for CLI tools
$toolsDir = $PSScriptRoot

# Create tools subdirectories
$cliToolsDir = Join-Path $toolsDir "cli_tools"
if (-not (Test-Path $cliToolsDir)) {
    New-Item -ItemType Directory -Path $cliToolsDir | Out-Null
}

# Tool URLs and directories
$tools = @{
    "reshacker" = @{
        url = "http://www.angusj.com/resourcehacker/resource_hacker.zip"
        dir = "reshacker"
        exe = "ResourceHacker.exe"
        cli = "rhcli.exe"
    }
    "pe-bear" = @{
        url = "https://github.com/hasherezade/pe-bear-releases/releases/download/0.6.5.3/PE-bear_0.6.5.3_x64_win.zip"
        dir = "pe-bear"
        exe = "PE-bear.exe"
    }
    "rcedit" = @{
        url = "https://github.com/electron/rcedit/releases/download/v1.1.1/rcedit-x64.exe"
        dir = "rcedit"
        exe = "rcedit.exe"
    }
    "resource_extract" = @{
        url = "https://www.nirsoft.net/utils/resourcesextract.zip"
        dir = "resource_extract"
        exe = "ResourcesExtract.exe"
    }
    "7zip" = @{
        url = "https://www.7-zip.org/a/7z2301-x64.exe"
        dir = "7zip"
        exe = "7z.exe"
    }
}

# Download and setup function
function Setup-Tool {
    param (
        [string]$name,
        [hashtable]$config
    )
    
    Write-Host "Setting up $name..."
    $toolDir = Join-Path $cliToolsDir $config.dir
    
    try {
        # Create tool directory if it doesn't exist
        if (-not (Test-Path $toolDir)) {
            New-Item -ItemType Directory -Path $toolDir -Force | Out-Null
        }
        
        # Download tool
        $fileName = if ($config.url -match '\.exe$') { $config.exe } else { "$name.zip" }
        $downloadPath = Join-Path $toolDir $fileName
        
        Write-Host "Downloading $name to $downloadPath..."
        
        # Create parent directory if it doesn't exist
        $parentDir = Split-Path -Parent $downloadPath
        if (-not (Test-Path $parentDir)) {
            New-Item -ItemType Directory -Path $parentDir -Force | Out-Null
        }
        
        # Download file
        [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
        Invoke-WebRequest -Uri $config.url -OutFile $downloadPath -UseBasicParsing
        
        # Extract if zip
        if ($downloadPath -match '\.zip$') {
            Write-Host "Extracting $name..."
            Expand-Archive -Path $downloadPath -DestinationPath $toolDir -Force
            Remove-Item $downloadPath -Force
        }
        
        Write-Host "$name setup completed successfully"
    }
    catch {
        Write-Host "Error setting up $name: $($_.Exception.Message)"
    }
}

# Setup each tool
foreach ($tool in $tools.GetEnumerator()) {
    Setup-Tool -name $tool.Key -config $tool.Value
}

# Create batch files for easy CLI access
$batchFiles = @{
    "reshacker-cli" = @"
@echo off
"$cliToolsDir\reshacker\$($tools.reshacker.cli)" %*
"@
    "pe-bear-cli" = @"
@echo off
"$cliToolsDir\pe-bear\$($tools.pe_bear.exe)" -console %*
"@
    "rcedit-cli" = @"
@echo off
"$cliToolsDir\rcedit\$($tools.rcedit.exe)" %*
"@
    "resource-extract-cli" = @"
@echo off
"$cliToolsDir\resource_extract\$($tools.resource_extract.exe)" /scomma %*
"@
}

# Create batch files
foreach ($batch in $batchFiles.GetEnumerator()) {
    Set-Content -Path (Join-Path $toolsDir "$($batch.Key).bat") -Value $batch.Value
}

# Create PowerShell module for tool integration
$moduleContent = @"
# CliTools.psm1
`$toolsPath = '$cliToolsDir'

function Invoke-ResHacker {
    param(
        [Parameter(Mandatory=`$true)]
        [string]`$InputFile,
        [Parameter(Mandatory=`$true)]
        [string]`$Action,
        [string]`$ResourceType,
        [string]`$ResourceName,
        [string]`$OutputFile
    )
    
    `$reshackerPath = Join-Path `$toolsPath "reshacker\$($tools.reshacker.cli)"
    `$args = "-open `"`$InputFile`" -action `$Action"
    if (`$ResourceType) { `$args += " -res `$ResourceType" }
    if (`$ResourceName) { `$args += " -name `$ResourceName" }
    if (`$OutputFile) { `$args += " -save `"`$OutputFile`"" }
    
    & `$reshackerPath `$args
}

function Invoke-PeBear {
    param(
        [Parameter(Mandatory=`$true)]
        [string]`$InputFile,
        [string]`$Action = "analyze"
    )
    
    `$pebearPath = Join-Path `$toolsPath "pe-bear\$($tools.pe_bear.exe)"
    & `$pebearPath -console -`$Action "`$InputFile"
}

function Invoke-RcEdit {
    param(
        [Parameter(Mandatory=`$true)]
        [string]`$InputFile,
        [string]`$VersionString,
        [string]`$FileDescription,
        [string]`$ProductName
    )
    
    `$rceditPath = Join-Path `$toolsPath "rcedit\$($tools.rcedit.exe)"
    `$args = "`"`$InputFile`""
    if (`$VersionString) { `$args += " --set-version-string `"`$VersionString`"" }
    if (`$FileDescription) { `$args += " --set-file-description `"`$FileDescription`"" }
    if (`$ProductName) { `$args += " --set-product-name `"`$ProductName`"" }
    
    & `$rceditPath `$args
}

function Invoke-ResourceExtract {
    param(
        [Parameter(Mandatory=`$true)]
        [string]`$InputFile,
        [string]`$OutputDir,
        [string]`$ResourceType
    )
    
    `$extractorPath = Join-Path `$toolsPath "resource_extract\$($tools.resource_extract.exe)"
    `$args = "/filename `"`$InputFile`""
    if (`$OutputDir) { `$args += " /sFolder `"`$OutputDir`"" }
    if (`$ResourceType) { `$args += " /ResourceType `"`$ResourceType`"" }
    
    & `$extractorPath `$args
}

Export-ModuleMember -Function Invoke-ResHacker, Invoke-PeBear, Invoke-RcEdit, Invoke-ResourceExtract
"@

# Create PowerShell module
$moduleDir = Join-Path $toolsDir "CliTools"
if (-not (Test-Path $moduleDir)) {
    New-Item -ItemType Directory -Path $moduleDir | Out-Null
}
Set-Content -Path (Join-Path $moduleDir "CliTools.psm1") -Value $moduleContent

# Create module manifest
$manifestContent = @"
@{
    ModuleVersion = '1.0'
    GUID = 'f1f9c2a0-5f1a-4f1b-9c2a-0f1a4f1b9c2a'
    Author = 'Windsurf Tools'
    Description = 'CLI tools for resource extraction and analysis'
    PowerShellVersion = '5.1'
    RequiredModules = @()
    FunctionsToExport = @('Invoke-ResHacker', 'Invoke-PeBear', 'Invoke-RcEdit', 'Invoke-ResourceExtract')
    CmdletsToExport = @()
    VariablesToExport = @()
    AliasesToExport = @()
    PrivateData = @{
        PSData = @{
            Tags = @('CLI', 'Resources', 'Extraction', 'Analysis')
            ProjectUri = 'https://github.com/your-repo'
        }
    }
}
"@
Set-Content -Path (Join-Path $moduleDir "CliTools.psd1") -Value $manifestContent

# Create README
$readmeContent = @"
# CLI Tools for Resource Extraction and Analysis

This directory contains various command-line tools for resource extraction and analysis:

## Tools Included

1. Resource Hacker CLI
   - Extract/modify resources in .exe, .dll
   - Usage: reshacker-cli.bat [options]

2. PE-Bear CLI
   - Analyze and modify PE files
   - Usage: pe-bear-cli.bat [options]

3. RcEdit
   - Edit Electron app metadata
   - Usage: rcedit-cli.bat [options]

4. Resource Extract
   - Extract various resources (icons, bitmaps, etc.)
   - Usage: resource-extract-cli.bat [options]

## PowerShell Module

The CliTools PowerShell module provides easy access to all tools:

\`\`\`powershell
Import-Module .\CliTools

# Extract resources
Invoke-ResHacker -InputFile "app.exe" -Action "extract"

# Analyze PE file
Invoke-PeBear -InputFile "app.exe" -Action "analyze"

# Edit metadata
Invoke-RcEdit -InputFile "app.exe" -VersionString "1.0.0"

# Extract resources
Invoke-ResourceExtract -InputFile "app.exe" -OutputDir "output"
\`\`\`

## Batch Files

Each tool has a corresponding .bat file for direct CLI access:
- reshacker-cli.bat
- pe-bear-cli.bat
- rcedit-cli.bat
- resource-extract-cli.bat
"@
Set-Content -Path (Join-Path $toolsDir "CLI_TOOLS_README.md") -Value $readmeContent

Write-Host "Setup complete! Tools are available in $cliToolsDir"
Write-Host "Use the .bat files or PowerShell module for easy access"
Write-Host "See CLI_TOOLS_README.md for usage instructions"
