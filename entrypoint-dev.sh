#!/bin/bash
python3 manage.py makemigrations
python3 manage.py migrate
python3 manage.py syncdata sources/cfc-seed.json
python3 manage.py syncdata sources/cfc-law30.json
python3 manage.py runserver 0.0.0.0:8080