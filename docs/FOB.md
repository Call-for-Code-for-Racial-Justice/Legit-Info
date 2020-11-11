# File/Object Storage

The File/Object Storage (FOB) is an abstraction layer that stores the
legislation in either a file system, an object store, or both.  For
example, during development, you may choose to have a local file system
for your legislation, and then sync this with the object storage so
that others can test.  The environment variable can be set to "FILE" or
"OBJECT" to denote the one the application and cron job should use.

```console
export FOB_METHOD='FILE'
```

## File Storage

The files can be stored on a local or shared file system.  Set the
environment variable FOB_STORAGE to the directory you want to store
files in.  It is recommended that this be outside your GIT application
root directory to avoid git issues.

```console
export FOB_STORAGE="/home/yourname/Develop/fob-storage"
```

## Object Storage

The files can be stored on a local or shared file system.  Set the
environment variable FOB_STORAGE to the directory you want to store
files in.  It is recommended that this be outside your GIT application
root directory to avoid git issues.

This application was tested with IBM Cloud Object Storage:

export COS_ENDPOINT_URL="https://<cloud.domain>"
export COS_API_KEY_ID="<your api key>"
export COS_INSTANCE="<instance>"


## fob_stats: Show statistics about File/Object Storage

This command will show you the number of files/objects stored, categorized
by prefix (state), and suffix (extension).  This can be useful to confirm
the statistics of both FILE and OBJECT stores.

### Invoking the fob_stats command

You can use cron1 or cron2 scripts to set up the Pipenv environment
to run the job natively.
```console
[legit-info]$ ./cron1 fob_stats --mode BOTH
```

If you are in the Pipenv shell, you can use stage1 or stage2, as well.

```console
(cfc) [legit-info]$ ./stage1 fob_stats --mode BOTH
```


### Built-in Help for keywords and parameters

```console
[legit-info]$ ./cron1 fob_stats --help
**Using SQLite3**
usage: manage.py fob_stats [-h] [--prefix PREFIX] [--suffix SUFFIX]
                           [--after AFTER] [--mode MODE] [--limit LIMIT]
                           [--version] [-v {0,1,2,3}] [--settings SETTINGS]
                           [--pythonpath PYTHONPATH] [--traceback]
                           [--no-color] [--force-color] [--skip-checks]

See Location and Impact database tables.

optional arguments:
  -h, --help            show this help message and exit
  --prefix PREFIX       Prefix of item names
  --suffix SUFFIX       Suffix of item names
  --after AFTER         Start after this item name
  --mode MODE           From FILE, OBJECT, or BOTH
  --limit LIMIT         Number of items to process
  --version             show program's version number and exit
  -v {0,1,2,3}, --verbosity {0,1,2,3}
                        Verbosity level; 0=minimal output, 1=normal output,
                        2=verbose output, 3=very verbose output
```

### Example output

Here is example output:

```console
[Yoga legit-info]$ ./cron1 fob_stats --mode BOTH
**Using SQLite3**
 
Mode =  FILE
By STATE
Number considered:  47028
Minimum: [AZ]  Maximum [US]
 
Top 10 List:
[US] had 30904 occurences
[AZ] had 9387 occurences
[OH] had 6732 occurences
[Other] had 5 occurences
 
By extension
Number considered:  47028
Minimum: [.html]  Maximum [.zip]
 
Top 10 List:
[.txt] had 23486 occurences
[.pdf] had 18829 occurences
[.html] had 4692 occurences
[.json] had 13 occurences
[.zip] had 8 occurences

Mode =  OBJECT
By STATE
Number considered:  47028
Minimum: [AZ]  Maximum [US]
 
Top 10 List:
[US] had 30904 occurences
[AZ] had 9387 occurences
[OH] had 6732 occurences
[Other] had 5 occurences
 
By extension
Number considered:  47028
Minimum: [.html]  Maximum [.zip]
 
Top 10 List:
[.txt] had 23486 occurences
[.pdf] had 18829 occurences
[.html] had 4692 occurences
[.json] had 13 occurences
[.zip] had 8 occurences
```


## fob_sync: Synchronize File/Object Storage

### Invoking the fob_stats command

You can use cron1 or cron2 scripts to set up the Pipenv environment
to run the job natively.
```console
[legit-info]$ ./cron1 fob_sync --maxdel 100 --maxput 100
```

If you are in the Pipenv shell, you can use stage1 or stage2, as well.

```console
(cfc) [legit-info]$ ./stage1 fob_sync --maxdel 100 --maxput 100
```

### Built-in Help for keywords and parameters

```console
[legit-info]$ ./cron1 fob_sync --help
**Using SQLite3**
usage: manage.py fob_sync [-h] [--prefix PREFIX] [--suffix SUFFIX]
                          [--after AFTER] [--only ONLY] [--maxdel MAXDEL]
                          [--maxget MAXGET] [--maxput MAXPUT] [--skip]
                          [--version] [-v {0,1,2,3}] [--settings SETTINGS]
                          [--pythonpath PYTHONPATH] [--traceback] [--no-color]
                          [--force-color] [--skip-checks]

Synchronize items in File/Object Storage. You can control the direction by
specifying --maxdel, --maxput and --maxget parameters. To make OBJECT look
like FILE, use --maxdel and --maxput only. To make FILE look like OBJECT, use
--maxget only.

optional arguments:
  -h, --help            show this help message and exit
  --prefix PREFIX       Prefix of names
  --suffix SUFFIX       Suffix of names
  --after AFTER         Start after this name
  --only ONLY           Process this name only
  --maxdel MAXDEL       Number of deletes from OBJECT storage
  --maxget MAXGET       Number of gets from OBJECT storage
  --maxput MAXPUT       Number of puts from OBJECT storage
  --skip                Skip copy if target exists already
  --version             show program's version number and exit
  -v {0,1,2,3}, --verbosity {0,1,2,3}
                        Verbosity level; 0=minimal output, 1=normal output,
                        2=verbose output, 3=very verbose output
```


### Example output

``` console
[legit-info]$ ./cron1 fob_sync --maxdel 10 --maxput 10
**Using SQLite3**
Starting fob_sync at Nov-11 06:17AM MST
Number of files found: 47028
Number of objects found: 47028

