# PowerShell script to extract UI files from SWF contents

# Create UI components directory structure
$uiRoot = "ui_components"
$directories = @(
    "base/core",
    "base/layout",
    "base/themes",
    "components/buttons",
    "components/windows",
    "components/menus",
    "components/hud",
    "assets/images/buttons",
    "assets/images/icons",
    "assets/images/backgrounds",
    "assets/images/borders",
    "assets/fonts",
    "assets/sounds",
    "screens/main",
    "screens/game",
    "screens/menus"
)

# Create directories
foreach ($dir in $directories) {
    New-Item -Path "$uiRoot/$dir" -ItemType Directory -Force
}

# Source directories
$swf1 = "./extracted/swf1_contents"
$swf2 = "./extracted/swf2_contents"
$swf3 = "./extracted/swf3_contents"
$swf4 = "./extracted/swf4_contents"
$swf5 = "./extracted/swf5_contents"

# Copy UI components
function Copy-UIComponents {
    param (
        [string]$source,
        [string]$destination,
        [string]$pattern
    )
    
    Get-ChildItem -Path $source -Recurse -Filter $pattern | 
    ForEach-Object {
        $destPath = Join-Path $destination $_.Name
        Copy-Item $_.FullName $destPath -Force
        Write-Host "Copied $($_.Name) to $destPath"
    }
}

# Extract UI components from each SWF
Write-Host "Extracting UI components..."

# From SWF1 (Core UI Framework)
Copy-UIComponents -source "$swf1/scripts" -destination "$uiRoot/base/core" -pattern "UI*.as"

# From SWF2 (Basic UI Components)
Copy-UIComponents -source "$swf2/scripts" -destination "$uiRoot/components" -pattern "*.as"
Copy-UIComponents -source "$swf2/images" -destination "$uiRoot/assets/images" -pattern "*.png"

# From SWF3 (Additional UI)
Copy-UIComponents -source "$swf3/scripts" -destination "$uiRoot/components" -pattern "*.as"

# From SWF4 (Game UI Components)
Copy-UIComponents -source "$swf4/scripts" -destination "$uiRoot/screens" -pattern "*View.as"
Copy-UIComponents -source "$swf4/images" -destination "$uiRoot/assets/images" -pattern "*.png"

# From SWF5 (Main Game UI)
Copy-UIComponents -source "$swf5/scripts/autoevony/gui" -destination "$uiRoot/components" -pattern "*.as"
Copy-UIComponents -source "$swf5/images/ui" -destination "$uiRoot/assets/images" -pattern "*.png"
Copy-UIComponents -source "$swf5/fonts" -destination "$uiRoot/assets/fonts" -pattern "*.ttf"
Copy-UIComponents -source "$swf5/sounds" -destination "$uiRoot/assets/sounds" -pattern "*.mp3"

Write-Host "UI components extraction complete!"

# Create manifest file
$manifest = @"
UI Components Manifest
=====================

Extracted: $(Get-Date)

Directory Structure:
$($directories | ForEach-Object { "- $_" } | Out-String)

Files:
$(Get-ChildItem $uiRoot -Recurse -File | ForEach-Object { "- $($_.FullName.Replace($uiRoot, ''))" } | Out-String)
"@

Set-Content -Path "$uiRoot/UI_MANIFEST.md" -Value $manifest

Write-Host "Manifest created at $uiRoot/UI_MANIFEST.md"
