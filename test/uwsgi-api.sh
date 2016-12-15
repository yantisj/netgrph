#!/bin/sh
export NGLIB_config_file="./netgrphdev.ini"
uwsgi --socket 0.0.0.0:9000 --protocol=http -w wsgi-api -H ./venv/
