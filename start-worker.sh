#!/bin/bash
export USE_SQLITE3='False'
cd /home/vcap/app
pipenv run manage2.py qcluster
