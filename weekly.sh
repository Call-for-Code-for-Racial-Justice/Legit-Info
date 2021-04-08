#!/bin/bash

# Use cron1 for SQLite3, and cron2 for PostgreSQL.
# --limit 0 means "unlimited" and will work on all files found

/app/cron1 get_datasets --api
/app/cron1 extract_files --api --skip --limit 0
/app/cron1 analyze_text --api --skip --compare --limit 0
