#!/usr/bin/env python3
import os
import sys


def is_venv():
    return (hasattr(sys, 'real_prefix') or
            (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix))

if __name__ == '__main__':
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cfc_project.settings')
    os.environ.setdefault('LD_LIBRARY_PATH', '/usr/local/lib')

    if not is_venv():
        print('Virtual Environment: ERROR **NOT FOUND**')
        print('Did you forget to activate your virtual environment?')
        print('To enter virtual environment:   pipenv shell')
        print('To exit virtual environment:    exit')
        sys.exit()

    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        print(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?", exc
        )
    execute_from_command_line(sys.argv)
