#!/bin/bash
# Development Environment Script
# 
# Start with source

#source ./docker/start-env.sh

export NG_config_file=netgrphdev.ini
export NG_dcmlib_loglevel=info
export NG_dcmlib_loglevel_ctl=info
export NG_LOG_STDOUT=1

export NG_nglib_dbpass=xxxx
export NG_nglib_dbhost=localhost

. ./venv/bin/activate
