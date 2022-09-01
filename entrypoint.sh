#!/bin/bash

if [[ ! -z ${POSTGRESQL_DATABASE_FILE} ]]; then
  export POSTGRESQL_DATABASE=`cat $POSTGRESQL_DATABASE_FILE`
fi
if [[ ! -z ${POSTGRESQL_USER_FILE} ]]; then
  export POSTGRESQL_USER=`cat $POSTGRESQL_USER_FILE`
fi
if [[ ! -z ${POSTGRESQL_PASSWORD_FILE} ]]; then
  export POSTGRESQL_PASSWORD=`cat $POSTGRESQL_PASSWORD_FILE`
fi

python3 manage.py makemigrations
python3 manage.py migrate
python3 manage.py loaddata sources/cfc-seed.json

TEST="${USE_SQLITE3:-False}"
if [[ "${TEST,,}" == "true" ]]; then
  python3 manage.py runserver 0.0.0.0:8080
else
  gunicorn -b 0.0.0.0:8080 --env DJANGO_SETTINGS_MODULE=cfc_project.settings cfc_project.wsgi --timeout 120
fi