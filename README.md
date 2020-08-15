# Emb(race): Policy and Legislation Reform

Technology has the power to drive action. And right now, a call to action is
needed to eradicate racism. **Black lives matter.**

We recognize technology alone cannot fix hundreds of years of racial injustice
and inequality, but when we put it in the hands of the Black community and
their supporters, technology can begin to bridge a gap. To start a dialogue.
To identify areas where technology can help pave a road to progress.

This project is an effort to utilize technology to analyze, inform, and
develop policy to reform the workplace, products, public safety, and
legislation.

This is one of three open source projects underway as part of the [Call for 
Code Emb(race) Spot Challenge](https://github.com/topics/embrace-call-for-code) 
led by contributors from IBM and Red Hat.

## Problem statement

Concerned citizens and impacted residents don't have a straightforward way of 
knowing what or how policies and regulations impact them or what they can do 
in response.  A community leader could use this tool to help motivate their
social followers.  Our target user will be referred to as "advocate".

### Hills (who, what, and wow)

1. Advocates are aware of policy that is being considered that is 
highly impactful to them, without needing to follow every vote.

2. Advocates are able to understand the specific impact of proposed 
policy on them without being a legal expert.

3. Advocates are able to share opinions so they can influence policy 
decisions before they are finalized.

4. Advocates can easily ascertain the voting record themes or trend of their
elected officials and political candidates without prior knowledge of who
they are.

5. Policy makers have visibility into how diverse citizenry will be impacted
by multiple variations of a proposed policy.

# Our Solution - Fix Politics App

Fix Politics is a web-based application written in Python programming
language, using the Django framework and Bootstrap user interface styling. Its 
primary goal is to help advocates find and summarize legislation based on an
advocate's preferences for impact areas and geographical location. 

The application is customizable, allowing application staff to specify
the location hierarchy and impact categories.  Complex legislation is curated, 
resulting in classifying the location scope and impact area, with a brief 
laymen-readable title and summary.

By classifying legislation by impact and location, we hope to increase 
awareness of current and pending legislation and their ability to affect change 
through voting or other activism.

## Steps to deploy the Fix Politics application

### Staged Deployment

This project is designed for three deployment stages.

1. Development

In stage 1, each developer has their own copy of application code and
data, using SQLite3 that stores the entire database in a single file.
Django provides a development webserver to allow local testing.

2. Pre-Production

In stage 2, each developer has their own copy of application code, but
a shared database, using Postgresql running in the IBM Cloud.  The
developer can choose to use the Django development webserver, or try out
the production server called Gunicorn.  The difference is that Django
is designed for single-user, and Gunicorn for concurrent multiple users.

3. Production

In stage 3, the application is running in the IBM Cloud in one pod, using the
Postgresql running in the IBM Cloud from pre-production.  Updates to the
code are deployed using a Tekton pipeline.

#### Stage 1: Development

1. Download and install the following modules.

* [Git](https://git-scm.com/book/en/v2/Getting-Started-Installing-Git)

On some systems, you may have an out-dated version.  For example, Red Hat
Enterprise Linux 7 ships automatically with git version 1.8.3, but we
recommend version 2.22 or higher.  You can verify your git level with
this command:

```bash
[local ~]$ git --version
git version 2.28.0
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
[Grady ~]$ mkdir Dev
```


3. Clone this GitHub repo to your local environment.

Run the git command in your Development workspace directory.

```bash
[Grady ~]$ cd Dev
[Grady Dev]$ git clone https://github.com/Call-for-Code/Embrace-Policy-Reform.git
```

4. Running Django applications has been simplified with a `manage.py` file to
 avoid dealing with configuring environment variables to run your app. From 
your project root, you can download the project dependencies with:

```bash
pipenv install
```

4. Activate your project's virtual environment with:

```bash
pipenv shell
```

5. Run the application locally in one of the following two ways:

To run as a Development server (py and HTML changes will automatically be picked up):

```bash
./run
```

To run as a Production server (shut down and restart required to pick up changes):

```bash
./app.sh
```

6. Your application will be running at `http://localhost:3000`.  You can access the `/health` endpoint at the host to verify server and app health.

##### Debugging locally
To debug a Django project run `python manage.py runserver 3000` with DEBUG set to True in `settings.py` to start a native Django development server. This comes with the Django's stack-trace debugger, which will present runtime failure stack-traces. For more information, see [Django's documentation](https://docs.djangoproject.com/en/2.0/ref/settings/).

##### Setting up a Mailtrap account
To test the Send Results e-mail functionality, you can set up a free Mailtrap 
account using the steps below.

1. Go to [Mailtrap](https://mailtrap.io/) and sign up for a free account.

2. Go to your Demo Inbox and copy your credentials:
```bash
user_name => 'your_username',
password => 'your_password',
address => 'smtp.mailtrap.io',
domain => 'smtp.mailtrap.io',
port => '2525',
```

3. In your virtual environment, export your credentials:
```bash
export EMAIL_HOST='smtp.mailtrap.io'
export EMAIL_HOST_USER='your_username'
export EMAIL_HOST_PASSWORD='your_password'
export EMAIL_PORT='2525'
```

4. Start the app:
```bash
./run

or

./app.sh
```

5. When you click "Send Results" from the app, your results should be e-mailed
to your Mailtrap inbox.

#### Stage 2: Pre-Production

1. Download and install the following modules.

* [Gunicorn](https://docs.gunicorn.org/en/stable/index.html)

#### Stage 3: Development



## License

This sample application is licensed under the Apache License, Version 2. Separate third-party code objects invoked within this code pattern are licensed by their respective providers pursuant to their own separate licenses. Contributions are subject to the [Developer Certificate of Origin, Version 1.1](https://developercertificate.org/) and the [Apache License, Version 2](https://www.apache.org/licenses/LICENSE-2.0.txt).

[Apache License FAQ](https://www.apache.org/foundation/license-faq.html#WhatDoesItMEAN)
