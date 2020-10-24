# Cron Automation

To keep the cfc_app_law database up-to-date, we run an asynchronous
background script. The script is intended to be run weekly, and can
be scheduled as a "cron" job.

The script has three phases:

## Phase 1: Get Datasets from Legiscan API

In this phase, we check to see if the current "DatasetList" is recent
enough (within the last 7 days) to be used "as is".  If it is a week
or more old, we will fetch a fresh one by invoking the "getDatasetList"
command to Legiscan.

A legislative session can last a few months, up to two years.  Legit-Info
determines how many legislative sessions are needed for the past 3 years.
This application determine which legislative sessions we need for
the past three years, and fetch individual datasets for each of those.

The DatasetLists and Dataset files are JSON format stored in 
[File/Object Storage](FOB.md).  Subsequent weekly run of this CRON job
will compare hash codes and the pre-existence of DatasetList and Dataset
files to avoid calling Legiscan API unnecessarily. 

### 1.1 Processing Logic

The application keeps five versions of the DatasetList, and so they are
named:  DatasetList-YYYY-MM-DD.json  (you can override the frequency by
using the --frequency parameter)

The DatasetList has a list of all legislative sessions for the past few
years for all 50 states, the US congress, and Washington DC.  Each location
is designed by a Legiscan_id, two-letter code abbreviation.  The list of
these can be found in /cfc_app/LegiscanAPI.py if you need them.

The django database "cfc_app_location" will designed which locations are
to be processed by having a valid (non-zero) legiscan_id.  For example,
id=3 represents Arizona, id=35 represents Ohio, and id=52 represents USA.

You may limit the processing to a single state using the --state parameter.

Each legislative session is identified by a unique session_id (NNNN), so 
the Datasets saved from Legiscan API are named SS-Dataset-NNNN.json, where
'SS' is the state code (AZ for Arizona, for example), and NNNN is four-digit
number representing the session_id.  Each session has a year_start and 
year_end.  To get legislation for 2018, 2019 and 2020, we get all sessions
that have a year_end 2018 or later.

If we have previously fetched the dataset, it might have been updated, so
we compare the hashcode in the DatasetList with the hashcode for this 
session_id we keep in the Django cfc_app_hash database table.

If the hashcodes match, there is no need to call the Legiscan API, we
are assured there have been no updates since the previous week for this
session.

The Legiscan.com API only allows 30,000 fetches per 30-day period, so
we have optimized this application to minimize calls to the Legiscan API.

### 1.2 Invoking the script for this phase

You can invoke this in either "on demand" or as part of a "cron" job
If you leave out the --api, the Legiscan.com API will not be invoked,
this is useful to see the status of existing Dataset JSON files, and
will identify any files not found.

You can use cron1 or cron2 scripts to set up the Pipenv environment
to run the job natively.
```console
[legit-info]$ ./cron1 get_datasets --api --state AZ
```

If you are in the Pipenv shell, you can use stage1 or stage2, as well.

```console
(cfc) [legit-info]$ ./stage1 get_datasets --api --state AZ
```

Cron Job:

```console
/home/yourname/Develop/legit-info/cron1 get_datasets --api
```

### 1.2 Built-in Help for keywords and parameters

```console
[legit-info]$ ./cron1 get_datasets --help
**Using SQLite3**
usage: manage.py get_datasets [-h] [--api] [--state STATE]
                              [--frequency FREQUENCY]

For each state in the United States listed in cfc_app_law database table, this
script will fetch the most recent legislative sessions, and create a JSON-
formatted output file SS-NNNN.json where 'SS' is the two-letter state
abbreviation like AZ or OH, and 'NNNN' is the four-digit session_id assigned
by Legiscan.com API. The SS-NNNN.json files are stored in File/Object Storage.

optional arguments:
  -h, --help            show this help message and exit
  --api                 Invoke Legiscan.com API
  --state STATE         Process single state: AZ, OH
  --frequency FREQUENCY Days since last DatasetList request
```

### 1.2 Example output

```console
[legit-info]$ cdf; ./cron1 get_datasets
**Using SQLite3**
Downloading:  DatasetList-2020-10-24.json
Verifying JSON contents of:  DatasetList-2020-10-24.json
Processing: United States (US)
Processing: Arizona, USA (AZ)
Processing: Ohio, USA (OH)
 
Item not found:  US-Dataset-1658.json
Item not found:  US-Dataset-1435.json
 
Session 1717 Year: 2020-2020 Date: 2020-08-30 Size: 4789832 bytes
Found session dataset:  AZ-Dataset-1717.json
Session 1623 Year: 2019-2019 Date: 2020-08-04 Size: 4647770 bytes
Found session dataset:  AZ-Dataset-1623.json
Session 1545 Year: 2018-2018 Date: 2020-08-04 Size: 48808 bytes
Found session dataset:  AZ-Dataset-1545.json
Session 1517 Year: 2018-2018 Date: 2020-08-04 Size: 4593193 bytes
Found session dataset:  AZ-Dataset-1517.json
 
Session 1646 Year: 2019-2020 Date: 2020-10-18 Size: 4256435 bytes
Found session dataset:  OH-Dataset-1646.json
Session 1422 Year: 2017-2018 Date: 2020-08-04 Size: 5754132 bytes
Found session dataset:  OH-Dataset-1422.json
```

## Phase 2: Extract Files

## Phase 3: Analyze Text

[IBM Watson Natural Language Understanding](IBM_NLU.md)
