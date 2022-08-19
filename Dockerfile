FROM python:3.9.13-slim-buster as base

# Setup env
ENV LANG C.UTF-8
ENV LC_ALL C.UTF-8
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONFAULTHANDLER 1


FROM base AS python-deps

# Install pipenv and compilation dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir pipenv gunicorn django whitenoise django_bootstrap4 django_extensions django_q psycopg2-binary django-allow-cidr

# Install python dependencies in /.venv
COPY Pipfile .
COPY Pipfile.lock .
RUN PIPENV_VENV_IN_PROJECT=1 pipenv install --deploy


FROM base AS runtime

# Install extra packages
RUN apt-get update && apt-get install -y --no-install-recommends postgresql-client iputils-ping && rm -rf /var/lib/apt/lists/*

# Copy virtual env from python-deps stage
COPY --from=python-deps /.venv /.venv
ENV PATH="/.venv/bin:$PATH"

# Create and switch to a new user
RUN useradd --create-home --uid 1001 --gid 0 appuser
WORKDIR /home/appuser

# Install application into container
COPY --chown=1001:0 . .
RUN chmod -R g=u .

USER appuser

EXPOSE 8080

CMD ["bash", "entrypoint.sh"]