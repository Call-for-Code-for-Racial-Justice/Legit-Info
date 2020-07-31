#!/bin/bash
gunicorn --env DJANGO_SETTINGS_MODULE=learning_logs.settings ./wsgi -b 0.0.0.0:3000
