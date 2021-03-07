#!/bin/bash
export PATH=/home/vcap/app/.local/bin:$PATH
curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
python3 get-pip.py
python3 -m pip install pipenv
pipenv install
which gunicorn
while true; do echo hello; sleep 10; done
