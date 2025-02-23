# PowerShell script to download and setup Adobe Flex SDK
$flexSdkUrl = "https://download.macromedia.com/pub/flex/sdk/flex_sdk_4.6.zip"
$flexDir = "flex_sdk"

Write-Host "Creating directories..."
New-Item -ItemType Directory -Force -Path $flexDir
New-Item -ItemType Directory -Force -Path "$flexDir\frameworks\libs\player\11.2"

Write-Host "Downloading Adobe Flex SDK..."
Invoke-WebRequest -Uri $flexSdkUrl -OutFile "flex_sdk.zip"
Write-Host "Extracting SDK..."
Expand-Archive -Path "flex_sdk.zip" -DestinationPath $flexDir -Force

Write-Host "Downloading Flash Player libraries..."
$playerGlobalUrl = "https://fpdownload.macromedia.com/get/flashplayer/updaters/11/playerglobal11_2.swc"
Invoke-WebRequest -Uri $playerGlobalUrl -OutFile "$flexDir\frameworks\libs\player\11.2\playerglobal.swc"

Write-Host "Cleaning up..."
Remove-Item -ErrorAction SilentlyContinue "flex_sdk.zip"

Write-Host "Setup complete!"
