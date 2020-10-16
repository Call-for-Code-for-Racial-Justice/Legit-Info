# Stage 3

## Stage 3: Production

1. Run Docker locally

Start the Docker daemon.

```bash
[ Dev]$ sudo systemctl start docker
```

2. Build Docker container from Dockerfile

```bash
[ Dev]$ cd legit-info
[ legit-info]$ ./build-docker 
Building legit-info:1.0.0
Sending build context to Docker daemon 38.22 MB
Step 1/24 : FROM registry.access.redhat.com/ubi8
 ---> a1f8c9699786
Step 2/24 : WORKDIR /app
 ---> Using cache
 ---> 65d3e1df9a22
Step 3/24 : COPY Pipfile* /app/
 ---> 9625d207c21e
Removing intermediate container d283ee3c4d17
Step 4/24 : USER root
 ---> Running in 9ee177d13f95
 ---> 5059268e72d1
Removing intermediate container 9ee177d13f95
Step 5/24 : RUN yum -y install python3
 ---> Running in 3876cd6d6c70

Updating Subscription Management repositories.
Unable to read consumer identity
Subscription Manager is operating in container mode.
Red Hat Universal Base Image 8 (RPMs) - BaseOS  559 kB/s | 768 kB     00:01
Red Hat Universal Base Image 8 (RPMs) - AppStre 2.3 MB/s | 3.9 MB     00:01
Red Hat Universal Base Image 8 (RPMs) - CodeRea  14 kB/s |  12 kB     00:00
Dependencies resolved.
==========================================================================================
 Package               Arch    Version                              Repository        Size
==========================================================================================
Installing:
 python36              x86_64  3.6.8-2.module+el8.1.0+3334+5cb623d7 ubi-8-appstream   19 k
Installing dependencies:
 platform-python-pip   noarch  9.0.3-16.el8                         ubi-8-baseos     1.8 M
 python3-pip           noarch  9.0.3-16.el8                         ubi-8-appstream   20 k
 python3-setuptools    noarch  39.2.0-5.el8                         ubi-8-baseos     163 k
Enabling module streams:
 python36                      3.6

Transaction Summary
==========================================================================================
Install  4 Packages

Total download size: 2.0 M
Installed size: 7.8 M
Downloading Packages:
(1/4): python36-3.6.8-2.module+el8.1.0+3334+5cb  49 kB/s |  19 kB     00:00
(2/4): python3-pip-9.0.3-16.el8.noarch.rpm      216 kB/s |  20 kB     00:00
(3/4): python3-setuptools-39.2.0-5.el8.noarch.r 259 kB/s | 163 kB     00:00
(4/4): platform-python-pip-9.0.3-16.el8.noarch. 1.9 MB/s | 1.8 MB     00:00
--------------------------------------------------------------------------------
Total                                           2.1 MB/s | 2.0 MB     00:00
Running transaction check
Transaction check succeeded.
Running transaction test
Transaction test succeeded.
Running transaction
  Preparing        :                                                        1/1 
  Installing       : python3-setuptools-39.2.0-5.el8.noarch                 1/4 
  Installing       : platform-python-pip-9.0.3-16.el8.noarch                2/4 
  Installing       : python36-3.6.8-2.module+el8.1.0+3334+5cb623d7.x86_64   3/4 
  Running scriptlet: python36-3.6.8-2.module+el8.1.0+3334+5cb623d7.x86_64   3/4 
  Installing       : python3-pip-9.0.3-16.el8.noarch                        4/4 
  Running scriptlet: python3-pip-9.0.3-16.el8.noarch                        4/4 
  Verifying        : platform-python-pip-9.0.3-16.el8.noarch                1/4 
  Verifying        : python3-setuptools-39.2.0-5.el8.noarch                 2/4 
  Verifying        : python36-3.6.8-2.module+el8.1.0+3334+5cb623d7.x86_64   3/4 
  Verifying        : python3-pip-9.0.3-16.el8.noarch                        4/4 
Installed products updated.

Installed:
  platform-python-pip-9.0.3-16.el8.noarch
  python3-pip-9.0.3-16.el8.noarch
  python3-setuptools-39.2.0-5.el8.noarch
  python36-3.6.8-2.module+el8.1.0+3334+5cb623d7.x86_64

Complete!
 ---> 7c2b653bc7ce
Removing intermediate container 3876cd6d6c70
Step 6/24 : RUN yum -y install python3-pip wget
 ---> Running in 2a0fe53e18e7

Updating Subscription Management repositories.
Unable to read consumer identity
Subscription Manager is operating in container mode.
Last metadata expiration check: 0:00:05 ago on Wed Aug 26 23:09:55 2020.
Package python3-pip-9.0.3-16.el8.noarch is already installed.
Dependencies resolved.
================================================================================
 Package     Architecture  Version                 Repository              Size
================================================================================
Installing:
 wget        x86_64        1.19.5-8.el8_1.1        ubi-8-appstream        735 k

Transaction Summary
================================================================================
Install  1 Package

Total download size: 735 k
Installed size: 2.9 M
Downloading Packages:
wget-1.19.5-8.el8_1.1.x86_64.rpm                735 kB/s | 735 kB     00:00
--------------------------------------------------------------------------------
Total                                           731 kB/s | 735 kB     00:01
Running transaction check
Transaction check succeeded.
Running transaction test
Transaction test succeeded.
Running transaction
  Preparing        :                                                        1/1 
  Installing       : wget-1.19.5-8.el8_1.1.x86_64                           1/1 
  Running scriptlet: wget-1.19.5-8.el8_1.1.x86_64                           1/1 
  Verifying        : wget-1.19.5-8.el8_1.1.x86_64                           1/1 
Installed products updated.

Installed:
  wget-1.19.5-8.el8_1.1.x86_64

Complete!
 ---> b6587c144843
Removing intermediate container 2a0fe53e18e7
Step 7/24 : RUN pip3 install --upgrade pip   && pip3 install --upgrade pipenv   && pipenv install --system --deploy
 ---> Running in e8a521942f21

WARNING: Running pip install with root privileges is generally not a good idea. Try `pip3 install --user` instead.
Collecting pip
  Downloading https://files.pythonhosted.org/packages/5a/4a/39400ff9b36e719bdf8f31c99fe1fa7842a42fa77432e584f707a5080063/pip-20.2.2-py2.py3-none-any.whl (1.5MB)
Installing collected packages: pip
Successfully installed pip-20.2.2
WARNING: pip is being invoked by an old script wrapper. This will fail in a future version of pip.
Please see https://github.com/pypa/pip/issues/5599 for advice on the underlying issue.
To avoid this problem you can invoke Python with '-m pip' instead of running pip directly.
Collecting pipenv
  Downloading pipenv-2020.8.13-py2.py3-none-any.whl (3.9 MB)
Collecting certifi
  Downloading certifi-2020.6.20-py2.py3-none-any.whl (156 kB)
Requirement already satisfied, skipping upgrade: setuptools>=36.2.1 in /usr/lib/python3.6/site-packages (from pipenv) (39.2.0)
Collecting virtualenv
  Downloading virtualenv-20.0.31-py2.py3-none-any.whl (4.9 MB)
Requirement already satisfied, skipping upgrade: pip>=18.0 in /usr/local/lib/python3.6/site-packages (from pipenv) (20.2.2)
Collecting virtualenv-clone>=0.2.5
  Downloading virtualenv_clone-0.5.4-py2.py3-none-any.whl (6.6 kB)
Collecting importlib-metadata<2,>=0.12; python_version < "3.8"
  Downloading importlib_metadata-1.7.0-py2.py3-none-any.whl (31 kB)
Collecting filelock<4,>=3.0.0
  Downloading filelock-3.0.12-py3-none-any.whl (7.6 kB)
Collecting appdirs<2,>=1.4.3
  Downloading appdirs-1.4.4-py2.py3-none-any.whl (9.6 kB)
Collecting importlib-resources>=1.0; python_version < "3.7"
  Downloading importlib_resources-3.0.0-py2.py3-none-any.whl (23 kB)
Collecting distlib<1,>=0.3.1
  Downloading distlib-0.3.1-py2.py3-none-any.whl (335 kB)
Requirement already satisfied, skipping upgrade: six<2,>=1.9.0 in /usr/lib/python3.6/site-packages (from virtualenv->pipenv) (1.11.0)
Collecting zipp>=0.5
  Downloading zipp-3.1.0-py3-none-any.whl (4.9 kB)
Installing collected packages: certifi, zipp, importlib-metadata, filelock, appdirs, importlib-resources, distlib, virtualenv, virtualenv-clone, pipenv
Successfully installed appdirs-1.4.4 certifi-2020.6.20 distlib-0.3.1 filelock-3.0.12 importlib-metadata-1.7.0 importlib-resources-3.0.0 pipenv-2020.8.13 virtualenv-20.0.31 virtualenv-clone-0.5.4 zipp-3.1.0
Installing dependencies from Pipfile.lock (33a0cd)…
 ---> 526671eec8e4
Removing intermediate container e8a521942f21
Step 8/24 : USER 1001
 ---> Running in 2d5bcaccf78d
 ---> a5dd9d5ec7eb
Removing intermediate container 2d5bcaccf78d
Step 9/24 : COPY . /app
 ---> 5072424041fa
Removing intermediate container 0368098b1cbb
Step 10/24 : USER root
 ---> Running in 31aa5a49a731
 ---> d63cad7e5b74
Removing intermediate container 31aa5a49a731
Step 11/24 : RUN mkdir -p /app/results &&   chmod ugo+w /app/results
 ---> Running in caa9c31380d9

 ---> bae7b8f7e10b
Removing intermediate container caa9c31380d9
Step 12/24 : USER 1001
 ---> Running in 08b2c5033808
 ---> 5c4e67aca319
Removing intermediate container 08b2c5033808
Step 13/24 : ENV USE_SQLITE3 "False"
 ---> Running in 72d00c43eb54
 ---> bd8e2457e4bb
Removing intermediate container 72d00c43eb54
Step 14/24 : ENV POSTGRESQL_DATABASE "cfcappdb"
 ---> Running in 6429f7a719e0
 ---> 3e4e34458d82
Removing intermediate container 6429f7a719e0
Step 15/24 : ENV POSTGRESQL_USER "NOT_SET"
 ---> Running in 27567d4e4b73
 ---> d3205667ae90
Removing intermediate container 27567d4e4b73
Step 16/24 : ENV POSTGRESQL_PASSWORD "NOT_SET"
 ---> Running in c067dfeb5259
 ---> 94eda9218836
Removing intermediate container c067dfeb5259
Step 17/24 : ENV POSTGRESQL_HOSTNAME "host.docker.internal"
 ---> Running in fa5e1b18d0e3
 ---> f8b3ce10052f
Removing intermediate container fa5e1b18d0e3
Step 18/24 : ENV POSTGRESQL_PORT 5432
 ---> Running in 522612ac1828
 ---> f0b23b0b5395
Removing intermediate container 522612ac1828
Step 19/24 : ENV EMAIL_HOST "NOT_SET"
 ---> Running in 34f4d46106bc
 ---> 398f5e4c1640
Removing intermediate container 34f4d46106bc
Step 20/24 : ENV EMAIL_PORT "NOT_SET"
 ---> Running in 160e42627cad
 ---> fed076a4e53f
Removing intermediate container 160e42627cad
Step 21/24 : ENV EMAIL_HOST_USER "NOT_SET"
 ---> Running in f44e2e89cae5
 ---> 7adaa20dcfb6
Removing intermediate container f44e2e89cae5
Step 22/24 : ENV EMAIL_HOST_PASSWORD "NOT_SET"
 ---> Running in 0d2674bcf324
 ---> 002959865927
Removing intermediate container 0d2674bcf324
Step 23/24 : EXPOSE 3000
 ---> Running in 6ea2a337eb79
 ---> 5d8050f203a3
Removing intermediate container 6ea2a337eb79
Step 24/24 : CMD gunicorn -b 0.0.0.0:3000 --env DJANGO_SETTINGS_MODULE=cfc_project.settings cfc_project.wsgi --timeout 120
 ---> Running in 34d4b0f4512c
 ---> 6177f65fdaf4
Removing intermediate container 34d4b0f4512c
Successfully built 6177f65fdaf4
```

3. Verify Docker Image built

```bash
[ Dev]$ cd legit-info
[ legit-info]$ docker image ls
REPOSITORY      TAG     IMAGE ID          CREATED             SIZE
legit-info    1.0.0   6177f65fdaf4      14 minutes ago      420 MB
```

4. Start and Stop Docker Image locally

Confirm that you can start the docker image locally.,

```bash
[ Dev]$ cd legit-info
[ legit-info]$ ./run-docker 
21ca1ad1ec07863f090f57b27af71e3964b712abe3e3a961d3d3659fd1354665
```

You can run your local browser with `http://localhost:3000` to confirm the
application is running.  The docker specifies USE_SQLITE3=False so that it
uses the Postgresql pod already running in the IBM Cloud.

To stop the application, you need to find the container id with `docker ps`
command, then use `docker stop` command with that value.

```bash
[ legit-info]$ docker ps
CONTAINER ID        IMAGE                COMMAND                  CREATED             STATUS              PORTS                    NAMES
21ca1ad1ec07        legit-info:1.0.0   "gunicorn -b 0.0.0..."   5 seconds ago       Up 3 seconds        0.0.0.0:3000->3000/tcp   peaceful_snyder
[ legit-info]$ docker stop 21ca1ad1ec07
21ca1ad1ec07

```

5. Build application pod in IBM Cloud

Now that you have validated the "Dockerfile" locally, we can use this to
build the application pod in the IBM Cloud.

Set "DEBUG = False" in cfc_project/settings.py

