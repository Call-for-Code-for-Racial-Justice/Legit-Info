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

This script keeps five versions of the DatasetList, and so they are
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

Each legislative session is identified by a unique session_id (SSS), so 
the Datasets saved from Legiscan API are named CC-Dataset-SSSS.json, where
'CC' is the state code (AZ for Arizona, for example), and SSSS is four-digit
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

### 1.3 Built-in Help for keywords and parameters

```console
[legit-info]$ ./cron1 get_datasets --help
**Using SQLite3**
usage: manage.py get_datasets [-h] [--api] [--state STATE]
                              [--frequency FREQUENCY]

Fetches DatasetList-YYYY-MM-DD.json from Legiscan.com, then for each location
listed in cfc_app_law database table with a valid Legiscan_id, this script
will fetch the most recent legislative sessions, and create a JSON-formatted
output file CC-Dataset-NNNN.json where 'CC' is the Legiscan location code like
AZ or OH, and 'NNNN' is the four-digit session_id assigned by Legiscan.com
API. The DatasetList and Dataset files are stored in File/Object Storage.

optional arguments:
  -h, --help            show this help message and exit
  --api                 Invoke Legiscan.com API
  --state STATE         Process single state: AZ, OH
  --frequency FREQUENCY Days since last DatasetList request
```

### 1.4 Example output

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

In this phase, we read the datasets from phase 1 for each legislative
session.  A legislative session can last a few months, up to two years.

The source (PDF or HTML) files and the resulting text files are stored in 
[File/Object Storage](FOB.md).  Subsequent weekly run of this CRON job
will compare hash codes and the pre-existence of source files to avoid 
calling Legiscan API unnecessarily. 

### 2.1 Processing Logic

This script reads the datasets fetched or updated from Legiscan in phase 1.
The dataset contains JSON with base64-encoded ZIP file inside.  The
ZIP is extracted, and each entry contains information unique to each
bill, including the documents associated with the bill text itself.

A bill might have mutilple documents.  For example, a version as the
bill was first introduced, a second version as amended during discussion, 
and a third version from the final vote.  We are only interested in the
latest version.

A unique key is generated for each bill, using the following scheme:
CC-BODYnnnn-SSSS-Yyyyy: 

* CC is the state abbreviation, AZ for Arizona, OH for Ohio, etc.
* BODYnnnn is the bill number, such as HB123 for the House, SB456 for Senate
* SSSS is the session_id assigned by Legiscan for this legislative session
* yyyy is the year this bill was first introduced.  With some legislative
sessions spanning 2 years, there bould be versions from both years for this
bill.  We want to avoid creating separate keys as the bill evolves.

The source file is fetched from the state's own website.  This could be
PDF or HTML format.  For PDF files, the PDFminer.six libraries are used
to extract the text.  For HTML files, the BeautifulSoup libraries are used.
The extracted text is cleaned up for acronyms that might confuse the 
natural language processor.  For example, "H. B. No. 345" is simplified to
"HB345" to avoid unnecessary periods that might denote the end of sentences.

The extracted text will will have some meta-data information in the front,
including the source file name, Legiscan's bill_id, the latest document date,
Legiscan hashcode for comparison, the source URL from state website, and
the title/summary as submitted by the state to Legiscan when uploaded.

```console
_FILE_ AZ-SB1154-1517-Y2018.html _BILLID_ 1057593 _DOCDATE_ 2018-01-11 
_HASHCODE_ dfcbc19fa9c56cd54024497330e8b090 
_CITE_ https://www.azleg.gov/legtext/53leg/2r/bills/sb1154p.htm 
_TITLE_ Technical Correction; Agricultural Landfills
_SUMMARY  Technical correction; agricultural landfills  _TEXT_ 
```

Sometimes the title and summary are identical, indicating the state employee
decided just to type in the minimal amount of information when sending in
the document.

The rest of the text is separated into sentences, using NLTK library,
so that each sentence is on its own line.  This will be used by Phase 3.

### 2.2 Invoking the script for this phase

You can invoke this in either "on demand" or as part of a "cron" job.

If you leave out the --api, the Legiscan.com API will not be invoked.
For the most part, we do not need it in this phase, as we have gotten
the state-link to the source file in phase 1.  However, in a few cases,
the state website might be down, or the individual bill withdrawn or
missing.  In this case, the Legiscan API can be invoked to fetch the
Legiscan version of the bill using the getBillText API call. Specifying
the --api will allow the Legiscan API to be called up to 10 times per
run.  Leaving out the --api will skip those bills not available from
the state website.

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

### 2.3 Built-in Help for keywords and parameters

Most of the parameters allow you to limit what is actually processed, by
state, by session, or by individual bill number.  You can see the help
for these by specifying -h or --help on the command.

```console
[...]$ cdf; ./cron1 analyze_text.py --help
**Using SQLite3**
Unknown command: 'analyze_text.py'. Did you mean analyze_text?
Type 'manage.py help' for usage.
[Yoga legit-info]$ cdf; ./cron1 extract_files --help
**Using SQLite3**
[nltk_data] Downloading package punkt to /home/tpearson/nltk_data...
[nltk_data]   Package punkt is already up-to-date!
usage: manage.py extract_files [-h] [--api] [--state STATE]
                               [--session_id SESSION_ID] [--bill BILL]
                               [--limit LIMIT] [--skip] [--version]
                               [-v {0,1,2,3}] [--settings SETTINGS]
                               [--pythonpath PYTHONPATH] [--traceback]
                               [--no-color] [--force-color] [--skip-checks]

For each state, scan the associated CC-Dataset-SSSS.json fetching the
legislation as either HTML or PDF file, and extract to TEXT. Both the original
(HTML/PDF) and the extracted TEXT file are stored in File/Object Storage, so
that they can be compared by developers to validate the text analysis.

optional arguments:
  -h, --help            show this help message and exit
  --api                 Invoke Legiscan.com API, if needed
  --state STATE         Process single state: AZ, OH
  --session_id SESSION_ID
                        Process this session only
  --bill BILL           Process this bill number only
  --limit LIMIT         Number of bills to extract per state
  --skip                Skip files already in File/Object storage
  --version             show program's version number and exit
  -v {0,1,2,3}, --verbosity {0,1,2,3}
                        Verbosity level; 0=minimal output, 1=normal output,
                        2=verbose output, 3=very verbose output
```

### 2.4 Example output

Be default, verbosity level 1, progress is indicated by a series of dots(.)
and arrows(>) for each bill processed.  You can quiet this with verbosity 
level 0, or display the full key with verbosity level 2.

Note, if you do no specify --skip parameter, the script will re-evaluate
every PDF or HTML file and over-write the text file.  If you specify the
--skip parameter, it will check the hashcodes, and if they match, the text
file will not be over-written.

```console
(cfc) [legit-info]$ ./stage1 extract_files --limit 3000 --skip
**Using SQLite3**
[nltk_data] Downloading package punkt to /home/tpearson/nltk_data...
[nltk_data]   Package punkt is already up-to-date!
.....>.>.>.>.>.>.>.>.>.>.>.>.>.>.>.>.>.>.>.>.>.>.>.>.>.>.>.>.>.>.>.>.>.>.>.
.>.>.>.>.>.>.>.>.>.>.>.>.>.>.>.>.>.>.>.>.>.>.>.>.>.>.>.>.>.>.>.>.>.>.>.>.>
.>.>.>.>.>.>.>.>.>.>.>.>.>.>.>.>.>.>.>.>.>.>.>.>.>.>.>.>.>.>.>.>.>.>.>.>.>
.>.>.>.>.>.>.>.>.>.>.>.>.>.>.>.>.>.>.>.>.>.>.>.>.>.>.>.>.>.>.>.>.>.>.>.>.>.
.>.>.>.>.>.>.>.>.>.>.>.>.>.>.>.>.>.>...................
```

## Phase 3: Analyze Text

In this phase, we read the text files generated by phase 2 and stored in 
[File/Object Storage](FOB.md).  The [IBM Watson Natural Language 
Understanding](IBM_NLU.md) API is invoked to get the top "concept" relevant
terms.  A relevant term can be a single word; name of a state, county, or
city; or a phrase.  Some of the phrases might have specific meanings in
judicial, legislative, medical, or other industry terminology.

### 3.1 Processing Logic

### 3.2 Invoking the script for this phase

### 3.3 Built-in Help for keywords and parameters

```console
[...]$ ./cron1 analyze_text --help
**Using SQLite3**
usage: manage.py analyze_text [-h] [--api] [--state STATE] [--after AFTER]
                              [--limit LIMIT] [--version] [-v {0,1,2,3}]
                              [--settings SETTINGS] [--pythonpath PYTHONPATH]
                              [--traceback] [--no-color] [--force-color]
                              [--skip-checks]

For all text files found in File/Object storage, run the IBM Watson Natural
Language Understanding (NLU) API, generate relevant words or phrases, and
compare these to the 'wordmap.csv' table determine the impact of each
legislation.The wordmap.csv is stored in the /sources directory as part this
application.

optional arguments:
  -h, --help            show this help message and exit
  --api                 Invoke IBM Watson NLU API
  --state STATE         Process single state: AZ, OH
  --after AFTER         Start after this item name
  --limit LIMIT         Limit number of entries to detail

```

### 3.4 Example output
