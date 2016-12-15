#!/usr/bin/env python
# Copyright (c) 2016 "Jonathan Yantis"
#
#    This program is free software: you can redistribute it and/or  modify
#    it under the terms of the GNU Affero General Public License, version 3,
#    as published by the Free Software Foundation.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#    As a special exception, the copyright holders give permission to link the
#    code of portions of this program with the OpenSSL library under certain
#    conditions as described in each individual source file and distribute
#    linked combinations including the program with the OpenSSL library. You
#    must comply with the GNU Affero General Public License in all respects
#    for all of the code used other than as permitted herein. If you modify
#    file(s) with this exception, you may extend this exception to your
#    version of the file(s), but you are not obligated to do so. If you do not
#    wish to do so, delete this exception statement from your version. If you
#    delete this exception statement from all source files in the program,
#    then also delete it in the license file.
#
#
"""
Flask API Server
"""
import builtins
import sys
import os
import re
import logging
from logging.handlers import RotatingFileHandler
import configparser
from flask import Flask, jsonify, request, g, make_response
from flask_httpauth import HTTPBasicAuth
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_sqlalchemy import SQLAlchemy
import nglib

logger = logging.getLogger(__name__)

# Populated from config file
debug = 0

# Flask Limits for Safety
flask_limits = ["10000 per day", "2000 per hour", "100 per minute"]

# Initialize Configuration
config_file = None
if 'NGLIB_config_file' in os.environ:
    config_file = os.environ['NGLIB_config_file']
else:
    config_file = builtins.apisrv_CONFIG
config = configparser.ConfigParser()
config.read(config_file)

# Check for sane config file
if 'apisrv' not in config:
    print("Could not parse config file: " + config_file)
    sys.exit(1)

# Logging Configuration, default level INFO
logger = logging.getLogger('')
logger.setLevel(logging.INFO)
lformat = logging.Formatter('%(asctime)s %(name)s:%(levelname)s: %(message)s')

# Debug mode
if 'debug' in config['apisrv'] and int(config['apisrv']['debug']) != 0:
    debug = int(config['apisrv']['debug'])
    logger.setLevel(logging.DEBUG)
    logging.debug('Enabled Debug mode')

# Enable logging to file if configured
if 'logfile' in config['apisrv']:
    lfh = RotatingFileHandler(config['apisrv']['logfile'], maxBytes=(1048576*5), backupCount=3)
    lfh.setFormatter(lformat)
    logger.addHandler(lfh)

# STDOUT Logging defaults to Warning
if not debug:
    lsh = logging.StreamHandler(sys.stdout)
    lsh.setFormatter(lformat)
    lsh.setLevel(logging.WARNING)
    logger.addHandler(lsh)

# Create Flask APP
app = Flask(__name__)
app.config.from_object(__name__)
app.config.update(dict(
    DATABASE=os.path.join(app.root_path, config['apisrv']['database']),
    SQLALCHEMY_DATABASE_URI='sqlite:///' + os.path.join(app.root_path, config['apisrv']['database']),
    SQLALCHEMY_TRACK_MODIFICATIONS=False,
    #SECRET_KEY='development key',
    #USERNAME='dbuser',
    #PASSWORD='dbpass'
))

# Auth module
auth = HTTPBasicAuth()

# Database module
db = SQLAlchemy(app)

# Apply Rate limiting
limiter = Limiter(
    app,
    key_func=get_remote_address,
    global_limits=flask_limits
)

def get_bolt_db():
    """Store nglib database handle under thread"""
    bdb = getattr(g, '_boltdb', None)
    if bdb is None:
        bdb = g._boltdb = nglib.get_bolt_db()
    return bdb

def get_py2neo_db():
    """Store nglib database handle under thread"""
    pydb = getattr(g, '_py2neodb', None)
    if pydb is None:
        pydb = g._py2neodb = nglib.get_py2neo_db()
    return pydb

@app.before_request
def init_db():
    """Initialize Library on each request"""
    logging.debug('Getting Neo4j Database Connections')
    nglib.verbose = debug
    nglib.init_nglib(config_file, initdb=False)
    nglib.bolt_ses = get_bolt_db()
    g.neo4j_db_bolt = nglib.bolt_ses
    nglib.py2neo_ses = get_py2neo_db()
    g.neo4j_db_py2neo = nglib.py2neo_ses

@app.teardown_appcontext
def close_db(error):
    """Closes the database again at the end of the request."""
    if hasattr(g, 'sqlite_db'):
        g.sqlite_db.close()

    bolt_ses = getattr(g, 'neo4j_db_bolt', None)
    if bolt_ses is not None:
        logger.debug('Closing Neo4j Database Connection')
        g.neo4j_db = None
        nglib.bolt_ses = None
        bolt_ses.last_result = None
        bolt_ses.close()

    py2neo_ses = getattr(g, 'neo4j_db_py2neo', None)
    if py2neo_ses is not None:
        logger.debug('Closing Neo4j Database Connection')
        g.neo4j_db = None
        nglib.py2neo_ses = None
        py2neo_ses.last_result = None
        py2neo_ses = None


# Safe circular imports per Flask guide
import apisrv.errors
import apisrv.views
import apisrv.user
import apisrv.netdb


