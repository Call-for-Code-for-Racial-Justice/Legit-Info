@ECHO off
:: This script runs the application with SQLite3 (see STAGE1.md for details)
::
:: Examples:
:: stage1.bat runserver localhost:3000   <--- default if nothing specified
:: stage1.bat shell
:: stage1.bat makemigrations
:: stage1.bat migrate
:: stage1.bat dbshell
:: stage1.bat qcluster

SET USE_SQLITE3='True'
SET parms="%*"
if [%parms%] == [""] ( SET parms=runserver localhost:3000 ) ELSE ( SET parms=%parms:"=%)
python manage.py %parms%
