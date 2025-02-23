@echo off
setlocal

REM Set paths
set "ANIMATE_PATH=C:\Program Files\Adobe\Adobe Animate 2021\Adobe Animate.exe"
set "OUTPUT_DIR=bin"
set "MAIN_CLASS=src/com/evony/useful/Main.as"

REM Create output directory if it doesn't exist
if not exist "%OUTPUT_DIR%" mkdir "%OUTPUT_DIR%"

REM Check for Adobe Animate
if not exist "%ANIMATE_PATH%" (
    echo Adobe Animate not found at "%ANIMATE_PATH%"
    echo Please install Adobe Animate or update the path
    exit /b 1
)

REM Create FLA file from template
echo Creating FLA file...
copy /y "templates\template.fla" "%OUTPUT_DIR%\RoboEvony.fla"

REM Set document class in FLA
echo Setting document class...
"%ANIMATE_PATH%" -e "fl.getDocumentDOM().docClass='Main'; fl.saveDocument(fl.getDocumentDOM()); fl.closeDocument(fl.getDocumentDOM());" "%OUTPUT_DIR%\RoboEvony.fla"

REM Publish SWF
echo Publishing SWF...
"%ANIMATE_PATH%" -p "%OUTPUT_DIR%\RoboEvony.fla"

REM Check if compilation was successful
if exist "%OUTPUT_DIR%\RoboEvony.swf" (
    echo Build successful! Output file: %OUTPUT_DIR%\RoboEvony.swf
    
    REM Create HTML wrapper
    echo Creating HTML wrapper...
    (
        echo ^<!DOCTYPE html^>
        echo ^<html^>
        echo ^<head^>
        echo     ^<title^>RoboEvony^</title^>
        echo ^</head^>
        echo ^<body^>
        echo     ^<object type="application/x-shockwave-flash" data="RoboEvony.swf" width="800" height="600"^>
        echo         ^<param name="movie" value="RoboEvony.swf" /^>
        echo         ^<param name="quality" value="high" /^>
        echo         ^<param name="bgcolor" value="#ffffff" /^>
        echo     ^</object^>
        echo ^</body^>
        echo ^</html^>
    ) > "%OUTPUT_DIR%\index.html"
) else (
    echo Build failed: Output SWF file not created
    exit /b 1
)

endlocal
