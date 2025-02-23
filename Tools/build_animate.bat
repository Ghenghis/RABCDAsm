@echo off
setlocal

REM Set paths
set OUTPUT_DIR=bin
set MAIN_CLASS=src/RoboEvonyMain.as

REM Create output directory if it doesn't exist
if not exist "%OUTPUT_DIR%" mkdir "%OUTPUT_DIR%"

REM Check for Adobe Animate installation
set ANIMATE_PATH="C:\Program Files\Adobe\Adobe Animate 2021\Adobe Animate.exe"
if not exist %ANIMATE_PATH% (
    echo Adobe Animate not found at %ANIMATE_PATH%
    echo Please install Adobe Animate or update the path
    exit /b 1
)

REM Compile ActionScript to SWF
echo Compiling ActionScript files...
%ANIMATE_PATH% -compile "%MAIN_CLASS%" -output "%OUTPUT_DIR%\RoboEvony.swf" -target 11.2

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
