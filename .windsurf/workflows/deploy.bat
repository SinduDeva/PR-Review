@echo off
REM PR Review Workflow - Easy Deployment Script (Windows)
REM Usage: deploy.bat "D:\project1" "D:\project2" ...

setlocal enabledelayedexpansion

if "%~1"=="" (
    echo ❌ No projects specified
    echo.
    echo Usage: %0 "D:\path\to\project1" "D:\path\to\project2" ...
    echo.
    echo Example:
    echo   %0 "D:\projects\affiliate-engine" "D:\projects\data-pipeline"
    exit /b 1
)

REM Get script directory
set "SCRIPT_DIR=%~dp0"

echo PR Review Workflow Deployment
echo ==============================
echo.
echo Source: %SCRIPT_DIR%
echo.

set "SUCCESSFUL=0"
set "FAILED=0"

REM Deploy to each project
:deploy_loop
if "%~1"=="" goto end_loop

set "PROJECT=%~1"

REM Resolve to absolute path
pushd "%PROJECT%" >nul 2>&1
if errorlevel 1 (
    echo ❌ Directory not found: %PROJECT%
    set /a FAILED+=1
    shift
    goto deploy_loop
)
set "PROJECT=!cd!"
popd >nul

echo → Deploying to: %PROJECT%

REM Create directories
if not exist "%PROJECT%\.windsurf\workflows\templates\" (
    mkdir "%PROJECT%\.windsurf\workflows\templates"
)

REM Copy workflow file
copy /Y "%SCRIPT_DIR%pr-review-comprehensive.md" "%PROJECT%\.windsurf\workflows\" >nul
if errorlevel 1 (
    echo ❌ Failed to copy workflow file
    set /a FAILED+=1
    shift
    goto deploy_loop
)

REM Copy template files
for %%F in ("%SCRIPT_DIR%templates\*.py") do (
    copy /Y "%%F" "%PROJECT%\.windsurf\workflows\templates\" >nul 2>&1
)

REM Create/update .gitignore
if exist "%PROJECT%\.gitignore" (
    find /i ".ai-review" "%PROJECT%\.gitignore" >nul 2>&1
    if errorlevel 1 (
        echo .ai-review/ >> "%PROJECT%\.gitignore"
    )
) else (
    echo .ai-review/ > "%PROJECT%\.gitignore"
)

echo ✅ Deployed to: %~n1
set /a SUCCESSFUL+=1

shift
goto deploy_loop

:end_loop
echo.
echo ==============================
echo ✅ Deployment Summary
echo Successful: %SUCCESSFUL%
echo Failed: %FAILED%
echo.

if %FAILED% equ 0 (
    echo ✅ All deployments completed successfully!
    exit /b 0
) else (
    echo ❌ Some deployments failed
    exit /b 1
)
