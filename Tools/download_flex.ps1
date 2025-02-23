# PowerShell script to download and setup Flex SDK
$flexUrl = "https://fpdownload.macromedia.com/get/flashplayer/updaters/32/playerglobal32_0.swc"
$flexDir = "flex_sdk"

# Create directories
New-Item -ItemType Directory -Force -Path $flexDir
New-Item -ItemType Directory -Force -Path "$flexDir\frameworks\libs\player\11.2"

# Download playerglobal.swc
Invoke-WebRequest -Uri $flexUrl -OutFile "$flexDir\frameworks\libs\player\11.2\playerglobal.swc"

Write-Host "Flex SDK setup complete"
