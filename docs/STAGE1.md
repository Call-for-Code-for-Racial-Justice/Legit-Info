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
[ ~]$ git --version
git version 2.28.0
```

* [Sqlite](https://www.djaodjin.com/blog/django-2-2-with-sqlite-3-on-centos-7.blog.html)

Stage 1 uses a local database called Sqlite3.  Tihs is popular because it
is a single file that works well with git repositories.  However, Django
requires Sqlite3 to be 3.8.3 to 3.25 (3.26 or higher causes problems).  The
default level of Sqlite3 on many Linux distributions is 3.7.17 and is used
by critical applications like YUM.  DO NOT UNINSTALL Sqlite 3.7.17, but rather
install Sqlite3 in /usr/local, and set your Operating System evironment
variables to reflect these changes.  This app was tested with 3.24 level.

```bash
[ ~]$ which sqlite3
/usr/bin/sqlite3

[ ~]$ sqlite3 --version
3.26.0 2018-12-01 12:34:55 bf8c1b2b7a5960c282e543b9c293686dccff272512d08865f4600fb58238alt1

[ ~]$ mkdir Sqlite3_24
[ ~]$ cd Sqlite3_24 

[ Sqlite3_24]$ wget https://www.sqlite.org/2018/sqlite-autoconf-3240000.tar.gz
[ Sqlite3_24]$ tar xvfz sqlite-autoconf-3240000.tar.gz
[ Sqlite3_24]$ cd sqlite-autoconf-3240000

[ sqlite-amalgamation-3240000]$ ./configure --prefix=/usr/local
[ sqlite-amalgamation-3240000]$ make
[ sqlite-amalgamation-3240000]$ sudo make install
```

Update your OS environment variables.  For example, add the following to 
your ~/.bashrc or /etc/bashrc file:

```
export PATH=/usr/local/sqlite/bin:$PATH
export LD_LIBRARY_PATH=/usr/local/sqlite/lib:$LD_LIBRARY_PATH
export LD_RUN_PATH=/usr/local/sqlite/lib:$LD_RUN_PATH
```

This will set the variables the next time you login.  Do refresh them
now, use the "source" command.  Confirm the version is now 3.24:

```bash
$ source ~/.bashrc
$ sqlite3 --version
3.24.0 2018-06-04 19:24:41 c7ee0833225bfd8c5ec2f9bf62b97c4e04d03bd9566366d5221ac8fb199a87ca
```

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

In addition to python3, you should have python3-pip which helps to install
other Python-related packages.

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

If not installed, use:

```bash
$ sudo pip3 install pipenv
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

To simplify, the rest of the instructions will assume a Red Hat Enterprise
Linux (RHEL) platform.  If you have Mac or Windows, you may need to make
adjustments to some commands.


3. Clone this GitHub repo to your local environment.

Run the git command in your Development workspace directory.  This will create
a new directory `/Dev/legit-info` which we will refer to as "project root" 

```bash
[ ~]$ cd Dev
[ Dev]$ git clone https://github.com/Call-for-Code-for-Racial-Justice/Legit-Info.git
```

IBM encourages everyone to use two-factor authorization for Github.  Generate
an ssh key and install it in your github account.  See [Connecting to Github with 
SSH]](https://docs.github.com/en/github/authenticating-to-github/connecting-to-github-with-ssh)

You can do git clone via SSH with these commands:

```bash
[ ~]$ cd Dev
[ Dev]$ git clone git@github.com:Call-for-Code-for-Racial-Justice/Legit-Info.git
```

4. The list of python dependencies needed for Djangjo, Bootstrap, and the
rest of this application are recorded in `Pipfile.lock` file.
From your project root, you can download and install the project 
dependencies into your virtual environment (virtualenv) with:

```bash
[ Dev]$ cd legit-Info
[ Legit-Info]$ pipenv install
```

5. Develop and test in this virtual environment.  Running Django applications
has been simplified with a `manage.py` program to avoid dealing with 
configuring environment variables to run your app. 

Several values are considered "secret" and should be stored in your 
Operating System environment variables instead of the Github repo.  In 
other cases, it is convenient to be able to change these values dynamically
while the system is running in production without have to modify the code.

For Linux, these can be put in your `~/.bashrc` or `/etc/bashrc` files.

* SECRET_KEY
* EMAIL_HOST
* EMAIL_HOST_USER
* EMAIL_HOST_PASSWORD
* EMAIL_PORT
* LEGISCAN_API_KEY
* CFC_DEBUG
* CFC_LOGLEVEL_DEV


For EMAIL settings, you can use Mailtrap.IO for testing.  When you sign up
for a free account, the SMTP Settings will give you the values you need to
set in your environment variables.

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
```

To generate SECRET_KEY, use this command:

```bash
[ legit-info]$ pipenv shell
(env) [ Legit-Info]$ python3
>>> from django.core.management.utils import get_random_secret_key
>>> print(get_random_secret_key())
r&3)a(64!9z_ftemuctw!whc_55(co-psxf1lj=w^x1a!ccqgb

```

Cut-and-paste the resulting key and add the following to your /etc/bashrc:

```bash
export SECRET_KEY='r&3)a(64!9z_ftemuctw!whc_55(co-psxf1lj=w^x1a!ccqgb'
```

For Stage 1, we will set the CFC_DEBUG='True' and CFC_LOGLEVEL_DEV='DEBUG'
so that we have verbose error messages during the development process.

```bash
export CFC_DEBUG='True'
export CFC_LOGLEVEL_DEV='DEBUG'
```

To start up the webserver for the application, use the "stage1" script:

```bash
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

7. To populate your databases, login as "cfcadmin".  Click on the "Impact"
option in the upper right, and the five Impact areas will be written to
your empty database.  Likewise, click on the "Location" option and the
"world", "usa', "arizona" and "ohio" locations will be created for you.

8. To populate the "Laws" database via automation, see the instructions
for [Cron Automation](CRON.md)

##### Debugging locally
To debug a Django project, run with DEBUG set to True in `settings.py` to 
start a native Django development server. This comes with the Django's 
stack-trace debugger, which will present runtime failure stack-traces. For 
more information, see [Django's 
documentation](https://docs.djangoproject.com/en/2.0/ref/settings/).






