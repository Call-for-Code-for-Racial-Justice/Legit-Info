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

EXPOSE 3000

CMD ["gunicorn", "-b", "0.0.0.0:3000", "--env", "DJANGO_SETTINGS_MODULE=pythondjangoapp.settings.production", "pythondjangoapp.wsgi", "--timeout 120"]
