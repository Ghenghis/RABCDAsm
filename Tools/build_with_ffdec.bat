@echo off
setlocal

REM Set paths
set FFDEC_PATH=.\ffdec_22.0.2
set SOURCE_DIR=src
set OUTPUT_DIR=bin
set MAIN_CLASS=src/RoboEvonyMain.as

REM Create output directory if it doesn't exist
if not exist "%OUTPUT_DIR%" mkdir "%OUTPUT_DIR%"

REM Compile ActionScript to SWF
echo Compiling ActionScript files...
call "%FFDEC_PATH%\ffdec_custom.bat" -compile "%SOURCE_DIR%" -output "%OUTPUT_DIR%\RoboEvony.swf" -format script "%MAIN_CLASS%"

if %ERRORLEVEL% EQU 0 (
    echo Build successful! Output file: %OUTPUT_DIR%\RoboEvony.swf
) else (
    echo Build failed with error code: %ERRORLEVEL%
)

endlocal
