FROM registry.access.redhat.com/ubi8

WORKDIR /app

COPY Pipfile* /app/

## NOTE - rhel enforces user container permissions stronger ##
USER root
RUN yum -y install python3
RUN yum -y install python3-pip wget

RUN pip3 install --upgrade pip \
  && pip3 install --upgrade pipenv \
  && pipenv install --system --deploy

USER 1001
COPY . /app

USER root
RUN mkdir -p /app/results && \
  chmod ugo+w /app/results

USER 1001
ENV USE_SQLITE3="False"
ENV POSTGRESQL_DATABASE="fixpoldb"
ENV POSTGRESQL_USER="NOT_SET"
ENV POSTGRESQL_PASSWORD="NOT_SET"
ENV POSTGRESQL_HOSTNAME="host.docker.internal"
ENV POSTGRESQL_PORT=5432


ENV EMAIL_HOST="NOT_SET"
ENV EMAIL_PORT="NOT_SET"
ENV EMAIL_HOST_USER="NOT_SET"
ENV EMAIL_HOST_PASSWORD="NOT_SET"



EXPOSE 3000

CMD ["gunicorn", "-b", "0.0.0.0:3000",  "cfc_project.wsgi", "--timeout 120"]
