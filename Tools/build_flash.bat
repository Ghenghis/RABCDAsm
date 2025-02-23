@echo off
setlocal

REM Set paths
set OUTPUT_DIR=bin
set MAIN_CLASS=src/RoboEvonyMain.as

REM Create output directory if it doesn't exist
if not exist "%OUTPUT_DIR%" mkdir "%OUTPUT_DIR%"

REM Copy files to output
xcopy /s /y src\* %OUTPUT_DIR%\
xcopy /s /y src\ui\* %OUTPUT_DIR%\ui\
xcopy /s /y src\core\* %OUTPUT_DIR%\core\
xcopy /s /y src\utils\* %OUTPUT_DIR%\utils\

REM Create HTML wrapper
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

echo Build complete! Open %OUTPUT_DIR%\index.html to test the application.

endlocal
