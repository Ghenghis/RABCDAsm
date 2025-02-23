@echo off
setlocal

REM Set paths
set AIR_SDK_HOME=air_sdk
set OUTPUT_DIR=bin
set MAIN_CLASS=src/RoboEvonyMain.as

REM Create output directory if it doesn't exist
if not exist "%OUTPUT_DIR%" mkdir "%OUTPUT_DIR%"

REM Download AIR SDK if not present
if not exist "%AIR_SDK_HOME%" (
    echo Downloading AIR SDK...
    powershell -Command "& { Invoke-WebRequest -Uri 'https://airsdk.harman.com/api/versions/33.1.1.698/download/AIR_Windows_SDK.zip' -OutFile 'air_sdk.zip' }"
    powershell -Command "& { Expand-Archive -Path 'air_sdk.zip' -DestinationPath '%AIR_SDK_HOME%' }"
    del air_sdk.zip
)

REM Compile ActionScript to SWF
echo Compiling ActionScript files...
"%AIR_SDK_HOME%\bin\mxmlc" ^
    -source-path=src ^
    -static-link-runtime-shared-libraries=true ^
    -target-player=11.2 ^
    -output="%OUTPUT_DIR%\RoboEvony.swf" ^
    "%MAIN_CLASS%"

if %ERRORLEVEL% EQU 0 (
    echo Build successful! Output file: %OUTPUT_DIR%\RoboEvony.swf
    
    REM Create HTML wrapper
    echo Creating HTML wrapper...
    echo ^<!DOCTYPE html^> > %OUTPUT_DIR%\index.html
    echo ^<html^> >> %OUTPUT_DIR%\index.html
    echo ^<head^> >> %OUTPUT_DIR%\index.html
    echo     ^<title^>RoboEvony^</title^> >> %OUTPUT_DIR%\index.html
    echo ^</head^> >> %OUTPUT_DIR%\index.html
    echo ^<body^> >> %OUTPUT_DIR%\index.html
    echo     ^<object type="application/x-shockwave-flash" data="RoboEvony.swf" width="800" height="600"^> >> %OUTPUT_DIR%\index.html
    echo         ^<param name="movie" value="RoboEvony.swf" /^> >> %OUTPUT_DIR%\index.html
    echo         ^<param name="quality" value="high" /^> >> %OUTPUT_DIR%\index.html
    echo         ^<param name="bgcolor" value="#ffffff" /^> >> %OUTPUT_DIR%\index.html
    echo     ^</object^> >> %OUTPUT_DIR%\index.html
    echo ^</body^> >> %OUTPUT_DIR%\index.html
    echo ^</html^> >> %OUTPUT_DIR%\index.html
) else (
    echo Build failed with error code: %ERRORLEVEL%
)

endlocal
