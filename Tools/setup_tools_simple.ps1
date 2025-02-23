# Setup script for CLI tools
$ErrorActionPreference = "Stop"

# Get absolute paths
$toolsDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$cliToolsDir = Join-Path $toolsDir "cli_tools"

Write-Host "Tools directory: $toolsDir"
Write-Host "CLI Tools directory: $cliToolsDir"

# Create tools directory
if (-not (Test-Path -LiteralPath $cliToolsDir)) {
    New-Item -ItemType Directory -Path $cliToolsDir -Force | Out-Null
}

# Tool URLs and configurations
$tools = @{
    "reshacker" = @{
        url = "https://downloads.sourceforge.net/project/reshacker/resource_hacker.zip"
        type = "zip"
        exe = "ResourceHacker.exe"
    }
    "pe-bear" = @{
        url = "https://github.com/hasherezade/pe-bear-releases/releases/download/0.6.5.3/PE-bear_0.6.5.3_x64_win.zip"
        type = "zip"
        exe = "PE-bear.exe"
    }
    "rcedit" = @{
        url = "https://github.com/electron/rcedit/releases/download/v1.1.1/rcedit-x64.exe"
        type = "exe"
        exe = "rcedit.exe"
    }
    "pesieve" = @{
        url = "https://github.com/hasherezade/pe-sieve/releases/download/v0.3.5/pe-sieve64.exe"
        type = "exe"
        exe = "pe-sieve64.exe"
    }
    "hxd" = @{
        url = "https://mh-nexus.de/downloads/HxDSetup.zip"
        type = "zip"
        exe = "HxD.exe"
    }
}

# Function to safely create directory
function New-SafeDirectory {
    param([string]$Path)
    if (-not (Test-Path -LiteralPath $Path)) {
        New-Item -ItemType Directory -Path $Path -Force | Out-Null
    }
}

# Function to safely download file
function Get-SafeWebFile {
    param(
        [string]$Uri,
        [string]$OutFile
    )
    try {
        [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
        $webClient = New-Object System.Net.WebClient
        $webClient.Headers.Add("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        $webClient.DownloadFile($Uri, $OutFile)
        Write-Host "Downloaded $Uri to $OutFile"
    }
    catch {
        Write-Host "Error downloading $Uri : $($_.Exception.Message)"
        throw
    }
}

# Download and setup tools
foreach ($tool in $tools.GetEnumerator()) {
    Write-Host "Setting up $($tool.Key)..."
    $toolDir = Join-Path $cliToolsDir $tool.Key
    New-SafeDirectory -Path $toolDir
    
    $fileName = if ($tool.Value.type -eq "zip") { "$($tool.Key).zip" } else { $tool.Value.exe }
    $filePath = Join-Path $toolDir $fileName
    
    try {
        Get-SafeWebFile -Uri $tool.Value.url -OutFile $filePath
        
        if ($tool.Value.type -eq "zip") {
            Expand-Archive -LiteralPath $filePath -DestinationPath $toolDir -Force
            Remove-Item -LiteralPath $filePath -Force
        }
        
        Write-Host "$($tool.Key) setup completed"
    }
    catch {
        Write-Host "Failed to setup $($tool.Key): $($_.Exception.Message)"
        continue
    }
}

# Create batch files
$batchFiles = @{}
foreach ($tool in $tools.GetEnumerator()) {
    $exePath = Join-Path (Join-Path $cliToolsDir $tool.Key) $tool.Value.exe
    $batchFiles["$($tool.Key)-cli.bat"] = "@echo off`r`n`"$exePath`" %*"
}

foreach ($batch in $batchFiles.GetEnumerator()) {
    $batchPath = Join-Path $toolsDir $batch.Key
    Set-Content -LiteralPath $batchPath -Value $batch.Value -Force
    Write-Host "Created batch file: $($batch.Key)"
}

Write-Host "Setup complete! Tools are available in $cliToolsDir"
Write-Host "Use the .bat files for easy access"

# Create a tools documentation file
$docsContent = @"
# Resource Analysis Tools

This directory contains various tools for analyzing and extracting resources from executables and game files.

## Available Tools

1. Resource Hacker (reshacker-cli.bat)
   - View and extract resources from PE files
   - Modify resource sections
   - Command-line interface available

2. PE-Bear (pe-bear-cli.bat)
   - PE file analysis and modification
   - Resource section viewer
   - Import/Export tables analysis
   - Console mode available

3. RcEdit (rcedit-cli.bat)
   - Command-line resource editor
   - Modify executable metadata
   - Update icons and version info

4. PE-Sieve (pesieve-cli.bat)
   - Process scanner
   - Detect and analyze suspicious PE modifications
   - Memory dumping capabilities

5. HxD (hxd-cli.bat)
   - Hex editor for raw binary analysis
   - Pattern finding
   - Data comparison

## Additional Recommended Tools

1. SWF Analysis:
   - SwfTools - Command-line tools for SWF manipulation
   - Flasm - ActionScript bytecode tool
   - AS3Lib - ActionScript 3 analysis

2. Asset Extraction:
   - AssetRipper - Unity asset extraction
   - QuickBMS - Game resource extraction
   - Ninja Ripper - 3D model extraction

3. Binary Analysis:
   - x64dbg - Advanced debugger
   - Radare2 - Reverse engineering framework
   - Cutter - GUI for Radare2

4. Network Analysis:
   - Fiddler - Web debugging proxy
   - Wireshark - Network protocol analyzer

## Usage Notes

1. All tools can be accessed via their respective batch files
2. Some tools require additional configuration for specific file types
3. Check tool documentation for detailed usage instructions
4. Keep tools updated for best compatibility

## Tips for Resource Extraction

1. Always scan files with PE-Sieve before extraction
2. Use Resource Hacker for initial resource enumeration
3. PE-Bear helps understand file structure
4. HxD is useful for raw binary investigation
5. RcEdit for quick resource modifications

## Support

For additional tools or updates, check the respective GitHub repositories:
- PE-Bear: https://github.com/hasherezade/pe-bear
- PE-Sieve: https://github.com/hasherezade/pe-sieve
- Resource Hacker: http://www.angusj.com/resourcehacker/
"@

Set-Content -LiteralPath (Join-Path $toolsDir "TOOLS.md") -Value $docsContent -Force
Write-Host "Created tools documentation in TOOLS.md"
