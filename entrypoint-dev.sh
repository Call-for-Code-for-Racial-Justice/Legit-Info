#!/bin/bash
python3 manage.py makemigrations
python3 manage.py migrate
python3 manage.py loaddata sources/cfc-seed.json
python3 manage.py runserver 0.0.0.0:8080