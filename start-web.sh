#!/bin/bash
export USE_SQLITE3='False'
cd /home/vcap/app
pipenv run gunicorn -b 0.0.0.0:$PORT --env DJANGO_SETTINGS_MODULE=cfc_project.settings cfc_project.wsgi
