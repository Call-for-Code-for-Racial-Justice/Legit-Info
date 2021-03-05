#!/usr/bin/env python3
""" This is the main program for Django """

import os
import sys

if __name__ == '__main__':
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cfc_project.settings')
    os.environ.setdefault('LD_LIBRARY_PATH', '/usr/local/lib')

    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        print(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?", exc
        )
    execute_from_command_line(sys.argv)
