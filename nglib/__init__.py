#!/usr/bin/env python
#
#
# Copyright (c) 2016 "Jonathan Yantis"
#
# This file is a part of NetGrph.
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
 NGDB Main Library
 - Main Library functions and variables used by modules
 - Call module.init_nglib(config) to initialize
 - Sets logging levels, loads config file
"""
import csv
import re
import sys
import os
import pwd
import datetime
import configparser
import logging

try:
    from neo4j.v1 import TRUST_ON_FIRST_USE, TRUST_SIGNED_CERTIFICATES, SSL_AVAILABLE
    from neo4j.v1.exceptions import CypherError, ProtocolError
    from neo4j.v1 import GraphDatabase, basic_auth
    from py2neo import Node, Relationship, Graph
except ImportError:
    pass


logger = logging.getLogger(__name__)

# Global variables (all library global variables go here)
verbose = 0
config = None

# Save user for library
user = pwd.getpwuid(os.getuid())[0]

# DB Sessions accessed globally
bolt_ses = None
py2neo_ses = None

# Topology Variables
max_distance = 100
dev_seeds = None

# NetDB Enabled
use_netdb = False

def get_bolt_db():
    """Return Bolt Session"""

    # DB Credentials
    dbuser = config['nglib']['dbuser']
    dbpass = config['nglib']['dbpass']
    dbhost = config['nglib']['dbhost']

    return get_db_client(dbhost, dbuser, dbpass, bolt=True)

def get_py2neo_db():
    """Return Bolt Session"""

    # DB Credentials
    dbuser = config['nglib']['dbuser']
    dbpass = config['nglib']['dbpass']
    dbhost = config['nglib']['dbhost']

    return get_db_client(dbhost, dbuser, dbpass, bolt=False)

def get_db_client(dbhost, dbuser, dbpass, bolt=False):
    """Return a Neo4j DB session. bolt=True uses bolt driver"""    

    if verbose > 4:
        print("DB Creds", dbhost, dbuser, dbpass)

    if bolt:
        bolt_url = "bolt://" + dbhost
        auth_token = basic_auth(dbuser, dbpass)
        try:
            driver = GraphDatabase.driver(bolt_url, auth=auth_token, max_pool_size=5)
            bolt_session = driver.session()
            return bolt_session
        except Exception as e:
            print("Database connection/authentication error:", e)
            sys.exit(1)
    else:
        login = "http://{0}:{1}@{2}:7474/db/data/".format(dbuser, dbpass, dbhost)
        py2neo_session = Graph(login)
        return py2neo_session

def drop_database():
    """Drop all database data (requires a full import to restore)"""

    logger.warning('Dropping Database')

    bolt_ses.run("MATCH ()-[e]-() DELETE e")
    bolt_ses.run("MATCH (n) DELETE n")


def import_cypher(fileName):
    """Import MATCH/CREATE/MERGE Cypher Commands Directly"""
    f = open(fileName)

    for line in f:
        if re.search(r'^(MATCH|CREATE|MERGE)', line):
            line = line.strip()
            logger.debug(line)
            results = bolt_ses.run(line)

            test = results.consume()
            if test:
                logger.info('Executed ' + test.statement)

def get_time(hours=None):
    """Get current time, optionally time shifted by hours"""

    if hours:
        timeShifted = datetime.datetime.now() - datetime.timedelta(hours=hours)
        return str(timeShifted)

    time = str(datetime.datetime.now())
    return time


def getEntry(l, pos=0):
    """Returns first entry in a list, or at position pos=x"""

    return l[pos]


def importCSVasDict(fileName):
    """Imports a file with DictReader"""

    f = open(fileName)
    db = csv.DictReader(f)
    return db


def importCSVasList(fileName):
    """Imports CSV File as a list"""

    f = open(fileName)
    flist = csv.DictReader(f)

    return flist


# Initialize Configuration
def init_nglib(configFile, initdb=True):
    """Initializes Library based on config file

    - Sets global variables in library for use with other modules
    - Configures debugging and sets up logging
    - Modifies py2neo and bolt library levels

    """

    # Global variables for use throughout library
    global config
    global max_distance
    global dev_seeds
    global bolt_ses
    global py2neo_ses
    global use_netdb

    if verbose > 1:
        print("Config File", configFile)

    config = configparser.ConfigParser()
    config.read(configFile)

    # Initialize Logging
    init_logging()

    # Tries to Loads NetDB Variables
    try:
        use_netdb = config['netdb']['host']
    except KeyError:
        pass
    if use_netdb:
        use_netdb = True

    if initdb:
        # DB Credentials
        dbuser = config['nglib']['dbuser']
        dbpass = config['nglib']['dbpass']
        dbhost = config['nglib']['dbhost']

        # Login to DB for parent Variables
        if verbose > 1:
            logger.info("Connecting to Neo4j: %s %s", dbhost, dbuser)
        bolt_ses = get_db_client(dbhost, dbuser, dbpass, bolt=True)
        py2neo_ses = get_db_client(dbhost, dbuser, dbpass)

    # Topology
    max_distance = int(config['topology']['max_distance'])
    dev_seeds = config['topology']['seeds']

    logger.debug("Initialized Configuration Successfully")


def init_logging():
    '''Initialize Logging'''
    # Default loglevel
    level = logging.INFO

    logfile = config['nglib']['logfile']
    loglevel = config['nglib']['loglevel']

    if loglevel == 'info':
        level = logging.INFO
    if loglevel == 'debug':
        level = logging.DEBUG
    if loglevel == 'debuglib':
        level = logging.DEBUG
    if loglevel == 'warning':
        level = logging.WARNING
    if loglevel == 'critical':
        level = logging.CRITICAL

    # Debug logging
    if verbose > 2:
        loglevel = 'debug'
        level = logging.DEBUG
    elif verbose > 1:
        loglevel = 'debuglib'
        level = logging.DEBUG

    # Verbose Logs to stdout
    if verbose:
        logging.basicConfig(format='%(asctime)s %(name)s:%(levelname)s: %(message)s',
                            stream=sys.stdout, level=level)
        logger.info("Enabled STDOUT Logging")

    # Log to File
    else:
        logging.basicConfig(format='%(asctime)s %(name)s:%(levelname)s: %(message)s',
                            filename=logfile, level=level)

    # Silence Cypher Logging
    if loglevel == 'info' or loglevel == 'debuglib':
        logging.getLogger("py2neo.cypher").setLevel(logging.WARNING)
        logging.getLogger("py2neo.batch").setLevel(logging.WARNING)
        logging.getLogger("httpstream").setLevel(logging.WARNING)
        logging.getLogger("neo4j.bolt").setLevel(logging.WARNING)
