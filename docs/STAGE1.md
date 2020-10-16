# Stage 1

## Stage 1: Development

Follow these steps to start development and testing on your local machine.

1. Download and install the following software:

* [Git](https://git-scm.com/book/en/v2/Getting-Started-Installing-Git)

On some systems, you may have an out-dated version.  For example, Red Hat
Enterprise Linux 7 ships automatically with git version 1.8.3, but we
recommend version 2.22 or higher.  You can verify your git level with
this command:

```bash
[local ~]$ git --version
git version 2.28.0
```

* [Sqlite](https://www.djaodjin.com/blog/django-2-2-with-sqlite-3-on-centos-7.blog.html)

Stage 1 uses a local database called Sqlite3.  Tihs is popular because it
is a single file that works well with git repositories.  However, Django
requires Sqlite3 to be 3.8.3 to 3.25 (3.26 or higher causes problems).  The
default level of Sqlite3 on many Linux distributions is 3.7.17 and is used
by critical applications like YUM.  DO NOT UNINSTALL Sqlite 3.7.17, but rather
install Sqlite3 in /usr/local, and set LD_LIBRARY_PATH to /usr/local/lib
so that Django can use the updated level.  This app was tested with 3.24 level.


* [Python](https://www.python.org/downloads/)

This application requires Python 3.6.1 or higher.  There are two levels
of Python, Python2 is incompatible with Python3.  For some operating 
systems, you may need to leave Python2 alone, and install Python3 along side
the older version.  DO NOT REMOVE Python2, AS IT MAY BE NEEDED BY YOUR
OPERATING SYSTEM.  Some applications like YUM on Red Hat Enterprise Linux
rely on Python2.  Often "python" points to the default level.  You can
verify what levels of Python you have using these commands:

```bash
[local ~]$ python --version
Python 2.7.5
[local ~]$ python2 --version
Python 2.7.5
[local ~]$ python3 --version
Python 3.6.8
```

* [Pipenv](https://pypi.org/project/pipenv/)

Pipenv is a tool that aims to bring the best of all packaging worlds with
Python's virtual environment.  It automatically creates and manages a 
virtualenv for your projects, as well as adds/removes packages from your 
Pipfile as you install/uninstall packages. It also generates the ever-important
Pipfile.lock, which is used to produce deterministic builds.

Deterministic builds eliminates that possibility of package dependency 
issues when switching from development to production systems.

The virtual environment allows the developer to add/remove packages in the
environment that may be different than their laptop deployment.  In this
manner, each Python application project can have its own set of python
package dependencies at different levels.

You can verify your level of pipenv with this command:

```bash
[legit-info]$ pipenv --version
pipenv, version 2020.6.2
```


2. Create Development workspace directory

We recommend you have a directory for development.  If you don't already
have such a directory, you can create one called "Dev".  In the examples
below, we use the name "Grady" to represent the user.

* On Windows, Grady would use:  C:\Users\Grady\Dev

```
C:\Users\Grady> mkdir Dev
```

* On Mac or Linux, for Grady's home directory:  /home/Grady/Dev

```
[ ~]$ mkdir Dev
```


3. Clone this GitHub repo to your local environment.

Run the git command in your Development workspace directory.  This will create
a new directory `/Dev/legit-info` which we will refer to as "project root" 

```bash
[ ~]$ cd Dev
[ Dev]$ git clone https://github.com/Call-for-Code/Embrace-Policy-Reform.git
```

IBM encourages everyone to use two-factor authorization for Github.  Generate
an ssh key and install it in your github account.  See [Connecting to Github with 
SSH]](https://docs.github.com/en/github/authenticating-to-github/connecting-to-github-with-ssh)

You can do git clone via SSH with these commands:

```bash
[ ~]$ cd Dev
[ Dev]$ git clone git@github.com:Call-for-Code-for-Racial-Justice/legit-info.git
```

4. The list of python dependencies needed for Djangjo, Bootstrap, and the
rest of this application are recorded in `Pipfile.lock` file.
From your project root, you can download and install the project 
dependencies into your virtual environment (virtualenv) with:

```bash
[ Dev]$ cd legit-info
[ legit-info]$ pipenv install
```

5. Develop and test in this virtual environment.  Running Django applications
has been simplified with a `manage.py` program to avoid dealing with 
configuring environment variables to run your app. 

Several values are considered "secret" and should be stored in your 
Operating System environment variables.  For Linux, these can be put
in your `~/.bashrc` or `/etc/bashrc` files.

```bash
SECRET_KEY
EMAIL_HOST
EMAIL_HOST_USER
EMAIL_HOST_PASSWORD
EMAIL_PORT
POSTGRESQL_DATABASE
POSTGRESQL_USER
POSTGRESQL_PASSWORD
POSTGRESQL_HOSTNAME
POSTGRESQL_PORT
LEGISCAN_API_KEY

```

To generate SECRET_KEY, use this command:
```
$ python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'
```

For EMAIL settings, you can use Mailtrap.IO for testing.  When you sign up
for a free account, the SMTP Settings will give you the values you need to
set in your environment variables.

Contact your Postgresql Administrator for the database name, user, password,
and port used.

For Legiscan API, you will need to register for a free account on 
Legiscan.com website.  The API fetches the legislation for United States.

While you are in the virtual environment, there will be an indicator such as 
"(env)" in front of your normal shell prompt.  Use "exit" to leave the 
virtual environment.  If you were using "python3" in your normal shell,
you only need to use "python" within your virtualenv.

```bash
[ legit-info]$ pipenv shell
Launching subshell in virtual environment…

We have created "stage1" script as a shortcut for 
the `python manage.py` command. 

Create Superuser on Postgresql.  You need at least one user to login
as andministrator.  For example, create "cfcadmin" and acceptable password.

(env) [ legit-info]$ ./stage1 createsuperuser
**Using SQLITE3**
Username (leave blank to use 'yourname'): cfcadmin
Email address: yourname@us.ibm.com
Password: <password here>
Password (again): <password here>
Superuser created successfully.

Now you are ready to run the application server.  Django provides a simple
webserver you can launch with a single one-line command.

(env) [legit-info]$ ./stage1 runserver localhost:3000
**Using SQLite3**
Performing system checks...
Django version 3.0.8, using settings 'cfc_project.settings'
Starting development server at http://localhost:3000/
Quit the server with CONTROL-C.

^C (env) [legit-info]$ exit
[ legit-info]$

```

6. Your application will be running at `http://localhost:3000` which
you can launch in your favorite browser (Chrome, Firefox, Safari, etc.)


##### Debugging locally
To debug a Django project, run with DEBUG set to True in `settings.py` to 
start a native Django development server. This comes with the Django's 
stack-trace debugger, which will present runtime failure stack-traces. For 
more information, see [Django's 
documentation](https://docs.djangoproject.com/en/2.0/ref/settings/).






