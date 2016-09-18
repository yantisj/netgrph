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
NetGrph NetDB IP Interface
"""
import re
import socket
import logging
import pymysql
import nglib.netdb
import nglib.ngtree


logger = logging.getLogger(__name__)


def get_netdb_ip(ip, hours=720):
    """Get All Details for an IP"""

    # Check for non-ip, try DNS
    if not re.search(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', ip):
        try:
            ip = socket.gethostbyname(ip)
        except socket.gaierror:
            raise Exception("Hostname Lookup Failure on: " + ip)

    netdb_ses = nglib.netdb.connect_netdb()

    lastseen = nglib.netdb.get_lastseen(hours)

    cursor = netdb_ses.cursor(pymysql.cursors.DictCursor)
    # cursor = netdb_ses.cursor(dictionary=True)

    cursor.execute("SELECT * FROM superarp "
                   + "WHERE ip = '{}' AND lastseen > '{}'".format(ip, lastseen))

    pc = cursor.fetchall()

    multi_entry = False
    pngtree = nglib.ngtree.get_ngtree("IPs", tree_type="NetDB")

    if not len(pc):
        return None

    # If multiple entries, primary returns under ngtree, the rest return
    # as historical nested data
    if len(pc) > 1:
        multi_entry = True

    latest = None

    # Gather details from DB in ngtree structure
    for en in pc:
        ngtree = nglib.ngtree.get_ngtree("IP", tree_type="NetDB")
        ngtree['Name'] = ip

        ngtree['firstSeen'] = str(en['firstseen'])
        ngtree['lastSeen'] = str(en['lastseen'])
        ngtree['MAC'] = en['mac']
        ngtree['FQDN'] = en['name']
        ngtree['vendor'] = en['vendor']
        ngtree['Switch'] = en['lastswitch']
        ngtree['SwitchPort'] = en['lastport']
        ngtree['UserID'] = en['userID']
        ngtree['VLAN'] = en['vlan']


        if not latest:
            latest = ngtree
        elif latest['lastSeen'] < ngtree['lastSeen']:
            latest = ngtree

        nglib.ngtree.add_child_ngtree(pngtree, ngtree)

        # Return as parent if single entry
        if not multi_entry:
            return ngtree

    # Return latest IP as root and nest others under a new tree
    multitree = nglib.ngtree.get_ngtree("Historical IPs", tree_type="NetDB")
    for en in pngtree:
        if '_child' in en and pngtree[en] != latest:
            nglib.ngtree.add_child_ngtree(multitree, pngtree[en])
    nglib.ngtree.add_child_ngtree(latest, multitree)
    return latest
