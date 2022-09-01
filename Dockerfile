FROM python:3.9.13-slim-buster as base

# Setup env
ENV LANG C.UTF-8
ENV LC_ALL C.UTF-8
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONFAULTHANDLER 1


FROM base AS python-deps

# Install pipenv and compilation dependencies
RUN pip install --no-cache-dir --upgrade pip==22.2.2 && \
    pip install --no-cache-dir pipenv==2022.8.24 gunicorn==20.1.0 django==4.1 django_bootstrap4==22.2 django_extensions==3.2.0 django-allow-cidr==0.5.0 django_q==1.3.9 psycopg2-binary==2.9.3 whitenoise==6.2.0

# Install python dependencies in /.venv
WORKDIR /
COPY Pipfile Pipfile.lock ./

RUN PIPENV_VENV_IN_PROJECT=1 pipenv install --deploy


FROM base AS runtime

# Create and switch to a new user
RUN useradd --create-home --uid 1001 --gid 0 appuser
WORKDIR /home/appuser

# Copy virtual env from python-deps stage
COPY --from=python-deps /.venv /.venv
ENV PATH="/.venv/bin:$PATH"

# Install application into container
COPY --chown=1001:0 . .
RUN chmod -R g=u .

USER appuser

EXPOSE 8080

CMD ["bash", "entrypoint.sh"]
