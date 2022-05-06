#!/bin/bash

# Use cron1 for SQLite3, and cron2 for PostgreSQL.
# --limit 0 means "unlimited" and will work on all files found

if [[ -z "${FOB_STORAGE}" ]]; then
	echo "Error: FOB_STORAGE environment variable not found"
	echo "Please set the FOB_STORAGE environment variable before running the script."
	exit 0
fi

if [[ -z "${LEGISCAN_API_KEY}" ]]; then
	echo "Error: LEGISCAN_API_KEY environment variable not found"
	echo "Please set the LEGISCAN_API_KEY environment variable before running the script."
	exit 0
fi

# change working directory to the one in which script resides
scriptPath=`dirname $0`
cd $scriptPath

./cron1 get_datasets --api
./cron1 extract_files --api --skip --limit 0
./cron1 analyze_text --api --skip --compare --limit 0
