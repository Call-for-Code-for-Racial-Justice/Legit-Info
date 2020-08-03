FROM registry.access.redhat.com/ubi8

WORKDIR /root

# Install Python
USER root
RUN yum -y install sudo grep
COPY MariaDB.repo /etc/yum.repos.d/
RUN yum -y install python3
RUN yum -y install python3-pip wget 
RUN yum -y install sqlite
RUN yum -y install openssl openssl-libs --nobest --skip-broken
RUN ls -al /usr/lib64/ | grep "libcrypt"
RUN ls -al /usr/lib64/ | grep "libssl"
#RUN yum -y install MariaDB-client --nobest --skip-broken
#RUN yum -y install mysql-client --nobest --skip-broken

RUN which python3 pip3 sqlite3 sudo

ENV LC_ALL=C.UTF-8
ENV LANG=C.UTF-8

RUN adduser -ms /bin/bash fixuser
RUN echo "fixuser:foxtrot.indigo.xray" | chpasswd
RUN find /usr/lib/python3.6/ -ls
RUN find /usr/lib64/python3.6/ -ls
RUN find /usr/local -ls
RUN mkdir -p /usr/local/lib && mkdir -p /usr/local/lib/python3.6/ && find /usr/local/lib/python3.6/ -ls


# Install Dependencies
WORKDIR /home/fixuser
USER fixuser

# Copy Code into Container
COPY . /home/fixuser
RUN python3 -m venv venv
RUN source venv/bin/activate && pip3 install --upgrade pip
RUN source venv/bin/activate && pip3 install -r requirements.txt
RUN source venv/bin/activate && exec app.sh

