@echo off
setlocal

REM -----------------------------------------------------------------------------
REM  configure_google_oauth.bat
REM  Helper script to create/update the .env file with Google OAuth credentials.
REM  Usage: double-click or run from a terminal after cloning the repo.
REM -----------------------------------------------------------------------------

cd /d "%~dp0"

echo This script will create/overwrite the local .env file with your credentials.
echo.
set /p GOOGLE_CLIENT_ID=Enter your Google Client ID (ends with .apps.googleusercontent.com): 
set /p GOOGLE_CLIENT_SECRET=Enter your Google Client Secret: 
echo.

(
  echo GOOGLE_CLIENT_ID=%GOOGLE_CLIENT_ID%
  echo GOOGLE_CLIENT_SECRET=%GOOGLE_CLIENT_SECRET%
) > ".env"

echo Done!  The .env file has been updated.
echo Restart "python manage.py runserver" to pick up the new values.
pause

