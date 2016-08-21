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
#
"""
Test Database functions for errors
"""
import os
import re
import sys
import argparse
import pytest
import subprocess

ngcmd = './netgrph.py' + ' '
upngcmd = './ngupdate.py' + ' '
ngrepcmd = './ngreport.py' + ' '

# Query Tests (cmd, result)
qtest = dict()
qtest['-dev core1'] = 'Child Neighbors'
qtest['-ip 10.9.46.1'] = 'Gateway'
qtest['-fp 10.1.120.50 8.8.8.8'] = 'ExternalFW'
qtest['-net 10.9.46.0/23 -o YAML'] = 'Router: xyz2mdf'
qtest['-nlist test_group'] = '10.9.46.0/23'
qtest['-group Core'] = 'core1'
qtest['-vid 120'] = '10.1.120.0/23'
qtest['-vtree ABC-120'] = '10.1.120.0/23'
qtest['-ip 10.9.136.1 -o JSON'] = '"IP": "10.9.136.1"'
qtest['-ip 10.9.136.1 -o YAML'] = 'IP: 10.9.136.1'
qtest['-sp xyz2mdf abc4mdf'] = 'core1'
qtest['-rp 10.1.108.50 10.1.20.50'] = 'core1'
qtest['-p 10.1.120.50 8.8.8.8'] = 'Description : Default Route'

# Production tests
ptest = dict()
ptest['-dev core1'] = 'Child Neighbors'
ptest['-ip 10.32.1.1'] = 'Gateway'
ptest['-fp 10.33.1.1 8.8.8.8'] = 'ExternalFW'
ptest['-net 10.32.0.0/17'] = 'wireless-GUEST'
ptest['-nlist security'] = '10.32.0.0/17'
ptest['-group Core'] = 'core1'
ptest['-vid 641'] = '10.32.0.0/17'
ptest['-vtree Core-641'] = '10.32.0.0/17'
ptest['-ip 10.32.1.1 -o JSON'] = '"IP": "10.32.1.1"'
ptest['-sp mdcmdf hvt404mdf'] = 'core1'
ptest['-rp 10.33.1.100 10.26.76.1'] = 'core1'
ptest['-p 10.26.72.142 10.26.72.17'] = 'From Switch : artmdf1'
ptest['-p 10.26.72.142 10.28.6.27'] = 'Link rVLANs'
ptest['-p 10.26.72.142 10.34.72.24'] = 'L4-HOP FW'

qtest = ptest

rtest = dict()
rtest['-vlans -empty -vrange 200'] = 'v6test'
#rtest['-vlans -vrange 120 -o yaml'] = 'Root: abc4mdf'
#rtest['-v -dev "xyz.*" -o json'] = '"parent_switch": "core1"'

# Update Tests (check for errors)
utest = ('-ivrf', '-id', '-ind', '-inet', '-isnet', '-iasa', '-ivlan', '-uvlan')

def run_query(cmd, option, result):
    """Run Queries for testing"""

    runcmd = cmd + option
    proc = subprocess.Popen([runcmd], stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        shell=True, universal_newlines=True)
    (out, err) = proc.communicate()

    if re.search(r'Traceback', err):
        print(err, file=sys.stderr)
        return False
    elif result and re.search(result, out):
        return True
    elif not result:
        return True
    else:
        return False


def test_queries():
    """netgrph query testing"""

    print("Testing Query Routines")

    for key in qtest.keys():
        print(key)
        assert(run_query(ngcmd, key, qtest[key])) == True

    for key in rtest.keys():
        print(key)
        assert(run_query(ngrepcmd, key, rtest[key])) == True


def test_updates():
    print("Testing Update Routines")

    for ut in utest:
        print(ut)
        assert(run_query(upngcmd, ut, None)) == True
