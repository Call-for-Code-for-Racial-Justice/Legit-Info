# Stage 2

## Stage 2: Pre-Production

1. Download and install the following modules.

* [Gunicorn](https://docs.gunicorn.org/en/stable/index.html)


2. Install all of the IBM Cloud and OpenShift command line tools.  Create
a file in your home directory called `.ibmcloud.yaml' that will contain
your IBM Cloud API token.

```bash
[ ~]$ cat .ibmcloud.yaml
accounts:
  sandbox: <your IBM Cloud API token here>
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
[ legit-info]$ icc embrace
Logging into ibmcloud: us-east/emb-race-team
Logging into OpenShift cluster: embrace-dev-ocp43-vpc
```

3. Create a Postgresql pod on IBM Cloud.  For our system, we created
the following:

```bash
Database name:  cfcappdb
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
[ legit-info]$ ./port-forward.sh
Use 'icc embrace' to log into IBM Cloud and OpenShift
API endpoint:      https://cloud.ibm.com
Region:            us-east
User:              tpearson@us.ibm.com
Account:           GSI Labs - IBM (7e341a8be8c9464e8778c7107b2bcccc) <-> 1924691
Resource group:    emb-race-team
CF API endpoint:
Org:
Space:
Using project "legit-info" on server
      "https://c100-e.us-east.containers.cloud.ibm.com:31358".
We will port forward 5432, do not close this terminal
Forwarding from 127.0.0.1:5432 -> 5432
Forwarding from [::1]:5432 -> 5432
```

5. Verify connection with command line

You can define an alias command as follows:

```bash
alias appdb='psql -h localhost -p 5432 -d cfcappdb -U pguser -w '
```

Explanation:

```
-h localhost --- this goes to the localhost, which port forwards to IBM Cloud
-p 5432      --- this is the port that Postgresql listens to
-d cfcappdb  --- this is the database name
-U pguser    --- this is the username 
-w           --- tells system to use PGPASSWORD environment variable
```

Now you can access the Postgresql database as follows:

```
[ ~]$ appdb
psql (10.14, server 10.12)
Type "help" for help.

cfcappdb=> help
You are using psql, the command-line interface to PostgreSQL.
Type:  \copyright for distribution terms
       \h for help with SQL commands
       \? for help with psql commands
       \g or terminate with semicolon to execute query
       \q to quit
cfcappdb=> \q
```

6. Pre-populate the Postgresql database tables.

Create Superuser on Postgresql.  Since we cannot copy data over from
SQlite3 to Postgresql, we will have to re-enter all the data using the 
application.  To get us started, we need to re-create the superuser 'cfcadmin'

```
(env) [ legit-info]$ ./stage2 createsuperuser
**Using Postgresql**
Username (leave blank to use 'yourname'): cfcadmin
Email address: yourname@us.ibm.com
Password: <password here>
Password (again): <password here>
Superuser created successfully.
```

As with Stage 1, selecting the "Location" will pre-populate the 
Locations with "world", "usa", "arizona" and "ohio".  Selecting
the "Impacts" will pre-populate with five imact areas.


Step 7: Run local version of Gunicorn.

The difference between the Django Development server (runserver) and
Gunicorn is that Gunicorn can handle concurrent users. We have created
a shortcut "app.sh" to run Gunicorn locally.  Gunicorn can be used with
local SQLite3 or remoe Postgresql, by specifying USE_SQLITE3 accordingly.

```
(env) [ legit-info]$ USE_SQLITE3=False ./app.sh
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

