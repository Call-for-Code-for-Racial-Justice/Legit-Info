#!/bin/bash
export USE_SQLITE3='False'
cd /home/vcap/app
python3 manage.py qcluster
