#!/usr/bin/env python
#
# NetGrph Export Routines
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
Helper functions to export ngtrees in the right format
"""
import logging
import json
import yaml
import csv
import sys
import nglib.ngtree

verbose = 0
logger = logging.getLogger(__name__)

def exp_ngtree(ngtree, rtype):
    """Prints or Returns NGTree in Requested format"""

    if rtype == "TREE":
        nglib.ngtree.print_ngtree(ngtree, dtree=dict())
    elif rtype == 'QTREE':
        exp_qtree(ngtree)
    elif rtype == "CSV":
        exp_CSV(ngtree)
    elif rtype == "JSON":
        exp_JSON(ngtree)
    elif rtype == "YAML":
        exp_YAML(ngtree)
    else:
        return ngtree

def exp_JSON(ngtree):
    """Prints an ngtree as JSON"""

    print(get_JSON(ngtree))

def get_JSON(ngtree):
    """Returns an ngtree as JSON Object"""

    jtree = json.dumps(ngtree, indent=2, sort_keys=True)
    return jtree

# Export as YAML
def exp_YAML(ngtree):
    """Prints an ngtree as YAML"""
    print(get_YAML(ngtree))

def get_YAML(ngtree):
    """Returns an ngtree as YAML Object"""
    ytree = yaml.dump(ngtree, Dumper=yaml.Dumper, default_flow_style=False)
    return ytree

def exp_qtree(ngtree):
    """Prints an ngtree with headers only"""

    stree = strip_ngtree(ngtree)

    nglib.ngtree.print_ngtree(stree, dtree=dict())


def cleanNGTree(ngtree):
    """Removes counts from output"""

    cleanND = ngtree.copy()
    cleanND.pop('_ccount', None)
    return cleanND

def exp_CSV(ngtree):
    """Attempts to Flatten JSON and dump as CSV"""

    ngjson = json.dumps(ngtree, sort_keys=True)

    fdict = tocsv(ngjson)

    for key in fdict.keys():
        print(key)

def _tocsv(obj, base=''):
    """Borrowed"""

    flat_dict = {}
    for k in obj:
        value = obj[k]
        if value is None:
            value = "None"
        if isinstance(value, dict):
            flat_dict.update(_tocsv(value, base + k + '.'))
        elif isinstance(value, (int, str, float, bool)):
            flat_dict[base + k] = value
        #elif value is None:
        #    print("None Value CSV", k, obj[k])
        else:
            raise ValueError("Can't serialize value of type "+ type(value).__name__)
    return flat_dict

def tocsv(json_content):
    """Dump JSON to CSV"""
    value = json.loads(json_content)
    if isinstance(value, dict):
        return _tocsv(value)
    else:
        raise ValueError("JSON root object must be a hash")

def strip_ngtree(ngtree, top=True):
    """Strips everything but headers from ngtree"""

    newtree = nglib.ngtree.get_ngtree(ngtree['Name'], tree_type=ngtree['_type'])

    for en in ngtree:
        if '_child' in en:
            newtree[en] = strip_ngtree(ngtree[en], top=False)
        elif top:
            newtree[en] = ngtree[en]

    return newtree
    