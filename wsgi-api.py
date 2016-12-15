#!/usr/bin/env python3
""" Run API Server as UWSGI App"""

from apisrv import app as application

if __name__ == "__main__":
    application.run()
