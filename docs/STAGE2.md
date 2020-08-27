# Fix Politics - Stage 2

## Stage 2: Pre-Production

1. Download and install the following modules.

* [Gunicorn](https://docs.gunicorn.org/en/stable/index.html)


2. Install all of the IBM Cloud and OpenShift command line tools.  Create
a file in your home directory called `.ibmcloud.yaml' that will contain
your IBM Cloud API token.

```bash
[Yoga ~]$ cat .ibmcloud.yaml
accounts:
  sandbox: <your IBM Cloud token here>
clusters:
  embrace:
    region: us-east
    resourceGroup: emb-race-team
    cluster: embrace-dev-ocp43-vpc
    account: sandbox
```

With this in place, you can login to both IBM Cloud and OpenShift
with a single command:

```bash
[Grady fix-politics]$ icc embrace
Logging into ibmcloud: us-east/emb-race-team
Logging into OpenShift cluster: embrace-dev-ocp43-vpc
```

3. Create a Postgresql pod on IBM Cloud.  For our system, we created
the following:

```bash
Database name:  fixpoldb
Postgresql username:  pguser
Postgresql password:  <provide an appropriate password>
```

Export the following OS Environment variables:

```bash
export POSTGRESQL_USER='pguser'
export POSTGRESQL_PASSWORD='<password here>'
export PGPASSWORD=$POSTGRSQL_PASSWORD
```

4. Forward the port 5432 to the IBM Cloud instance.  5432 is the standard
port for Postgresql.  Do not close this terminal, it will run indefinitely,
so push it aside, and use other terminal windows for the other tasks.

```bash
[Grady fix-politics]$ ./port-forward.sh
Use 'icc embrace' to log into IBM Cloud and OpenShift
API endpoint:      https://cloud.ibm.com
Region:            us-east
User:              tpearson@us.ibm.com
Account:           GSI Labs - IBM (7e341a8be8c9464e8778c7107b2bcccc) <-> 1924691
Resource group:    emb-race-team
CF API endpoint:
Org:
Space:
Using project "fix-politics" on server
      "https://c100-e.us-east.containers.cloud.ibm.com:31358".
We will port forward 5432, do not close this terminal
Forwarding from 127.0.0.1:5432 -> 5432
Forwarding from [::1]:5432 -> 5432
```

5. Verify connection with command line

You can define an alias command as follows:

```bash
alias fixdb='psql -h localhost -p 5432 -d fixpoldb -U pguser -w '
```

Explanation:

```
-h localhost --- this goes to the localhost, which port forwards to IBM Cloud
-p 5432      --- this is the port that Postgresql listens to
-d fixpoldb  --- this is the database name
-U pguser    --- this is the username 
-w           --- tells system to use PGPASSWORD environment variable
```

Now you can access the Postgresql database as follows:

```
[Grady ~]$ fixdb
psql (10.14, server 10.12)
Type "help" for help.

fixpoldb=> help
You are using psql, the command-line interface to PostgreSQL.
Type:  \copyright for distribution terms
       \h for help with SQL commands
       \? for help with psql commands
       \g or terminate with semicolon to execute query
       \q to quit
fixpoldb=> \q
```

6. Copy data from SQLite3 to Postgresql.  This application involves a
database with 17 tables.  If you want to populate the Postgresql data
in the IBM Cloud with the locations, impacts, and laws entered locally,
you must copy ALL data the from ALL 17 tables.

Environment variable "USE_SQLITE3" is available to choose between the local
SQLite3 database and the remote Postgresql database.

Here is the process:

Step 6a: Dump SQLite3 as JSON file.  Note that ** Using SQLite3 ** 
or **Using Postgresql **" is displayed, so the `sed` command is used
to remove this line.

```
[Grady Dev]$ cd fix-politics
[Grady fix-politics]$ pipenv shell
(fix) [Grady fix-politics]$ USE_SQLITE3='True' python manage.py dumpdata > db.json
(fix) [Grady fix-politics]$ sed -i '/..Using/d' db.json
```

Step 6b: Ensure Postgresql database is empty

```
(fix) [Grady fix-politics]$ USE_SQLITE3='False' python manage.py migrate
(fix) [Grady fix-politics]$ USE_SQLITE3='False' python manage.py shell
**Using PostgreSQL**
Python 3.6.8 (default, Sep 26 2019, 11:57:09) 
Type 'copyright', 'credits' or 'license' for more information
IPython 7.16.1 -- An enhanced Interactive Python. Type '?' for help.
In[1]: from django.contrib.contenttypes.models import ContentType
In[2]: ContentType.objects.all().delete()
In[3]: quit()
```

Step 6c: Load JSON file into Postgresql

```
(fix) [Grady fix-politics]$ USE_SQLITE3='False' python manage.py loaddata db.json
```


Step 7: Run local version of Gunicorn.

The difference between the Django Development server (runserver) and
Gunicorn is that Gunicorn can handle concurrent users. We have created
a shortcut "app.sh" to run Gunicorn locally.  Gunicorn can be used with
local SQLite3 or remoe Postgresql, by specifying USE_SQLITE3 accordingly.

```
(fix) [Yoga fix-politics]$ USE_SQLITE3=False ./app.sh
[2020-08-26 14:24:42 -0700] [23322] [INFO] Starting gunicorn 20.0.4
[2020-08-26 14:24:42 -0700] [23322] [INFO] Listening at: http://0.0.0.0:3000 (23322)
[2020-08-26 14:24:42 -0700] [23322] [INFO] Using worker: sync
[2020-08-26 14:24:42 -0700] [23325] [INFO] Booting worker with pid: 23325
**Using PostgreSQL**
```

As with the Django Development Server (runserver), press Ctrl-C to exit.

Step 8: Test from another system

If you have other systems, which could be a smartphone or template, on the
same network subnet, you can test Gunicorn from the other machine.

For example, if you are running Gunicorn on 192.168.1.3, then from your
smartphone or table, specify:  `http://192.168.1.3:3000`

If this does not work, you may need to change the settings in your network
firewall.







