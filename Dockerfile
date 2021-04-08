FROM registry.access.redhat.com/ubi8

WORKDIR /app

COPY Pipfile* /app/

## NOTE - rhel enforces user container permissions stronger ##
USER root
RUN yum -y install python3
RUN yum -y install python3-pip wget

RUN python3 -m pip install --user --upgrade pip
RUN python3 -m pip install --upgrade pipenv
RUN pipenv install --system --deploy

COPY . /app

RUN pwd
RUN chown -R 1001 /app
RUN chmod -R 775 /app

USER 1001

EXPOSE 8080
CMD ["gunicorn", "-b", "0.0.0.0:8080",  "--env", "DJANGO_SETTINGS_MODULE=cfc_project.settings", "cfc_project.wsgi", "--timeout 120"]
