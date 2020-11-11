#!/bin/bash

# Use cron1 for SQLite3, and cron2 for PostgreSQL.
# --limit 0 means "unlimited" and will work on all files found

/home/yourname/Dev/legit-info/cron1 get_datasets --api
/home/yourname/Dev/legit-info/cron1 extract_files --api --skip --limit 0
/home/yourname/Dev/legit-info/cron1 analyze_text --api --skip --compare --limit 0
