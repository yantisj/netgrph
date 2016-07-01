#!/usr/bin/env python
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
NetGrph Firewall Import Routines

- Need to remove ASA Parsing from file
"""
import re
import os
import logging
import nglib

verbose = 0
logger = logging.getLogger(__name__)

fwdir = None

def import_fw(fileName):
    """Import FW CSV File"""

    logger.info("Importing Firewalls from " + fileName)

    fwdb = nglib.importCSVasDict(fileName)

    # Import FW Ints to DB
    import_fw_ints(fwdb)


def import_fw_ints(fwdb):
    """Import Firewall Interfaces from FW File"""

    time = nglib.get_time()

    # Iterate through all firewall ints
    for fwint in fwdb:

        # DB Values
        name = fwint['Name']
        hostname = fwint['Hostname']
        IP = fwint['IP']
        vlanInt = fwint['Interface']
        desc = fwint['Description']
        seclevel = fwint['Security-Level']
        logIndex = fwint['Log-Index']

        #print(name, vlanInt, desc, seclevel, IP, hostname, logIndex)

        vlan = vlanInt.replace('Vlan', '')

        # Search for existing Firewall
        results = nglib.py2neo_ses.cypher.execute(
            'MATCH (fw:Switch:Router:FW {name:{name}}) RETURN fw',
            name=name)

        # Insert new Firewall
        if len(results) == 0:
            logger.info("Creating New Firewall: " + name)

            results = nglib.py2neo_ses.cypher.execute(
                'CREATE (fw:Switch:Router:FW {name:{name}, hostname:{hostname}, '
                + 'logIndex:{logIndex}, time:{time}}) RETURN fw',
                name=name, hostname=hostname, logIndex=logIndex, time=time)

        # Update FW
        else:
            logger.debug("Updating Firewall: " + name)

            nglib.py2neo_ses.cypher.execute(
                'MATCH (fw:Switch:Router:FW {name:{name}}) SET fw += '
                + '{hostname:{hostname}, logIndex:{logIndex}, time:{time}} RETURN fw',
                name=name, hostname=hostname, logIndex=logIndex, time=time)

        # Search for existing Vlan
        results = nglib.py2neo_ses.cypher.execute(
            'MATCH (n:Network {vid:{vlan}})-[e:ROUTED_FW]->'
            + '(fw:Switch:Router:FW {name:{name}}) '
            + 'RETURN e',
            vlan=vlan, name=name)

        if len(results) == 0:
            logger.info("Creating New ROUTED_FW Link: %s --> %s", vlan, name)

            results = nglib.py2neo_ses.cypher.execute(
                'MATCH (n:Network {vid:{vlan}}), (fw:Switch:Router:FW {name:{name}})'
                + 'CREATE (n)-[e:ROUTED_FW '
                + '{desc:{desc}, seclevel:{seclevel}, time:{time}}]->(fw)',
                vlan=vlan, name=name, desc=desc, seclevel=seclevel, time=time)

        # Update Firewall Interface
        else:
            logger.debug("Updating ROUTED_FW: %s --> %s", vlan, name)

            results = nglib.py2neo_ses.cypher.execute(
                'MATCH (n:Network {vid:{vlan}})-[e:ROUTED_FW]->'
                + '(fw:Switch:Router:FW {name:{name}})'
                + 'SET e += {desc:{desc}, seclevel:{seclevel}, time:{time}} '
                + 'RETURN e',
                vlan=vlan, name=name, desc=desc, seclevel=seclevel, time=time)
