@echo off
if not exist "%FLEX_HOME%" (
    echo ERROR: FLEX_HOME environment variable not set!
    echo Please install Adobe Animate or Flash Builder and set FLEX_HOME to point to the Flex SDK directory
    echo Example: set FLEX_HOME=C:\Program Files\Adobe\Adobe Animate 2021\Common\Configuration\ActionScript 3.0
    exit /b 1
)

echo Using Flex SDK from: %FLEX_HOME%
echo Building RoboEvony...

if not exist "bin" mkdir bin

"%FLEX_HOME%\bin\mxmlc" ^
    -source-path=src ^
    -static-link-runtime-shared-libraries=true ^
    -output=bin/RoboEvony.swf ^
    src/RoboEvonyMain.as

if %ERRORLEVEL% EQU 0 (
    echo Build successful! Output file: bin/RoboEvony.swf
) else (
    echo Build failed with error code: %ERRORLEVEL%
)
