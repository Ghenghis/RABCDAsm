@echo off
setlocal

REM Set paths
set FLEX_HOME=flex_sdk
set JAVA_HOME=C:\Program Files\Microsoft\jdk-17.0.14.7-hotspot
set OUTPUT_DIR=bin
set MAIN_CLASS=src/RoboEvonyMain.as

REM Create output directory if it doesn't exist
if not exist "%OUTPUT_DIR%" mkdir "%OUTPUT_DIR%"

REM Compile ActionScript to SWF using mxmlc
echo Compiling ActionScript files...
"%JAVA_HOME%\bin\java" -jar "%FLEX_HOME%\lib\mxmlc.jar" ^
    -load-config=flex-config.xml ^
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
