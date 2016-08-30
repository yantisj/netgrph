#!/usr/bin/env python3
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
"""
NetGrph NetDB Interface
"""

import datetime
import locale
import csv
import re
import os
import sys
import logging
import nglib
import pymysql

logger = logging.getLogger(__name__)

# DB connection is global
netdb_ses = None

def connect_netdb():
    """Update the netdb_ses handle"""

    global netdb_ses
    netdbhost = None
    netdbuser = None
    netdbpasswd = None

    try:
        netdbhost = nglib.config['netdb']['host']
        netdbuser = nglib.config['netdb']['user']
        netdbpasswd = nglib.config['netdb']['pass']

    except KeyError:
        print("Error: NetDB Database Credentials no Configured", file=sys.stderr)
        raise

    if not netdbuser:
        raise Exception("NetDB Credentials not Configured")

    netdb_ses = pymysql.connect(user=netdbuser, password=netdbpasswd,
                                host=netdbhost,
                                database="netdb")

    return netdb_ses


def get_lastseen(hours=168):
    """Get lastseen string for MySQL"""

    lastseen = datetime.datetime.now() - datetime.timedelta(hours=hours)
    lastseen = lastseen.isoformat()
    return lastseen


def get_mac_and_port_counts(switch, vlan):
    """Get the number of mac addresses and ports on a VLAN for a switch"""

    if not netdb_ses or not netdb_ses.open:
        connect_netdb()

    lastseen = get_lastseen()

    cursor = netdb_ses.cursor(pymysql.cursors.DictCursor)

    cursor.execute("SELECT count(vlan) AS pcount FROM switchstatus "
                   + "WHERE switch = '{}' and vlan='{}'".format(switch, vlan))

    pc = cursor.fetchall()
    pcount = pc[0]['pcount']

    # MACs on switch with lastseen
    mac_query = "SELECT count(mac) AS mcount FROM switchports "
    mac_query += "WHERE switch = '{}' AND s_vlan='{}' ".format(switch, vlan)
    mac_query += "AND lastseen > '{}'".format(lastseen)
    cursor.execute(mac_query)
    mc = cursor.fetchall()
    mcount = mc[0]['mcount']

    return(pcount, mcount)
