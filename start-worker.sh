#!/bin/bash
export USE_SQLITE3='False'
export PATH=/home/vcap/deps/0/python/bin:/home/vcap/deps/0/python/bin:$PATH
python3 -m pip install pipenv
cd /home/vcap/app
echo $PATH
which pipenv
ls -al
pipenv install
pipenv run ./manage.py qcluster
