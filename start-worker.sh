#!/bin/bash
export USE_SQLITE3='False'
export PATH=/home/vcap/.local/bin:$PATH
cd /home/vcap
curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
python3 get-pip.py
python3 -m pip install pipenv
cd /home/vcap/app
echo $PATH
which pipenv
ls -al
pipenv install
pipenv run ./manage.py qcluster
