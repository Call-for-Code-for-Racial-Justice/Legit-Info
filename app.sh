#!/bin/bash
gunicorn --env DJANGO_SETTINGS_MODULE=cfc_project.settings cfc_project.wsgi -b 0.0.0.0:3000
