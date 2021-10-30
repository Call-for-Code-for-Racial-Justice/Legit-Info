FROM registry.access.redhat.com/ubi8/python-38:1-71.1634036286

WORKDIR /opt/app-root/src

COPY --chown=1001:0 . .
RUN chmod -R g=u .

USER 1001

ENV LC_ALL=C.UTF-8 \
    LANG=C.UTF-8 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONFAULTHANDLER=1

# see issue https://github.com/pypa/pipenv/issues/4220 for pipenv version
RUN pip install --no-cache-dir --upgrade pip==21.3.1 && \
    pip install --no-cache-dir pipenv==2018.11.26 && \
    pipenv install --system --dev

EXPOSE 8080

ENTRYPOINT ["sh", "entrypoint.sh"]
CMD ["gunicorn", "-b", "0.0.0.0:8080",  "--env", "DJANGO_SETTINGS_MODULE=cfc_project.settings", "cfc_project.wsgi", "--timeout 120"]
