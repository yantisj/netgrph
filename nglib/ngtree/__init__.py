#!/usr/bin/env python
#
# Work with netgrph tree structures
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
Work with netgrph tree structures

ngtrees are nested dicts that convert to JSON/YAML

- Getting an ngtree will create a new unnested ngtree to populate with properties
- Adding a child ngtree will nest an ngtree under a parent
- Adding a parent ngtree will add a special parent ngtree for when you want
  the perspective of a certain tree level, but want to add a parent object

"""
import re
import datetime
import logging
#import nglib
from . import export

logger = logging.getLogger(__name__)

verbose = 0


def get_ngtree(name, tree_type="VLAN"):
    """Initialize an NGTree"""

    ngtree = dict()
    ngtree['Name'] = name
    ngtree['_type'] = tree_type

    return ngtree

def add_child_ngtree(ngtree, cngtree):
    """
    Nest a child ngtree under an ngtree

    Notes: Keeps track of child counts for easier parsing. Keys are named
           childXX where XX is the child number entry.

    """

    if '_ccount' not in ngtree.keys():
        ngtree['_ccount'] = 0

    ngtree['_ccount'] = ngtree['_ccount'] + 1
    ccount = ngtree['_ccount']
    if ccount < 10:
        cname = "_child00" + str(ccount)
    elif ccount < 100:
        cname = "_child0" + str(ccount)
    else:
        cname = "_child" + str(ccount)

    ngtree[cname] = cngtree


def add_parent_ngtree(ngtree, pngtree):
    """Add a special type parent ngtree existing ngtree"""

    ngtree['_parent'] = pngtree


def print_ngtree(ngtree, dtree, parent=False, depth=0, lasttree=False):
    """
    Recrusively print NGTrees using UTF-8 line drawing characters. If this
    causes terminal problems for you and you would prefer an ASCII only mode,
    contact me.

    Notes: This code is complicated, even to me. It should probably be rewritten,
    but basically, it nests multiple levels of ngtrees and their children in a
    pretty output format for use on the CLI.

    get_space_indent() gets output to prepend to lines to form the tree
    structure during output. It keeps track of where output is relative to the
    rest of the tree structure.

    The dtree dict keeps track of positions on tree to print continuations.

    The close out section needs to be better understood, but when closing out a
    child tree, you need to keep pipes from connecting sections below.

    There is a concept of Parent nodes, such as when you are doing a VID search,
    and want to build the tree from the current location, but also add in the
    Parent VID for context. Normally, Parent trees are not used.
    """

    hasParent = False

    dtree = dtree.copy()

    # Get indentation spaces variable based on depth
    spaces, indent = get_space_indent(depth, dtree)


    # Find Parent node if exists
    if '_parent' in ngtree.keys():
        dtree[0] = 1
        print_ngtree(ngtree['_parent'], dtree, parent=True)
        hasParent = True

    # Get indentation spaces variable based on depth
    spaces, indent = get_space_indent(depth, dtree)

    # Parent Nodes Print up top at the same level (see VID output)
    if parent:
        print("[Parent {:} {:}]".format(ngtree['_type'], ngtree['Name']))

    # Standard Node, Print Header
    else:
        if depth == 0 and not hasParent:
            indent = ""

        # Last tree terminates with └
        if lasttree:
            indent = indent.replace('├', '└')

        # Abbreviate certain types for shorter headers
        ngtype = ngtree['_type']
        if ngtype == "VLAN":
            ngtype = ""
        elif ngtree['_type'] == "Neighbor":
            ngtype = ""
        else:
            ngtype = " " + ngtype
        header = " "
        header = header.join([ngtype, ngtree['Name']])

        # Print section header -[header]
        if depth == 0:
            print("{:}┌─[{:} ]".format(indent, header))
            print("│")
        else:
            headonly = True
            for en in ngtree:
                if not re.search(r'Name|_type', en):
                    headonly = False
                    break
            if headonly:
                print("{:}──[{:} ]".format(indent, header))
            else:
                print("{:}┬─[{:} ]".format(indent, header))


    # Store Children as a list to be able to locate final child for indentation
    clist = []
    for key in sorted(ngtree.keys()):
        if re.search(r'^_child\d+', key):
            clist.append(key)

    # If there are no children, do not indent tree structure
    if len(clist) == 0:
        dtree.pop(depth, None)

    # Get indentation spaces variable based on current depth
    spaces, indent = get_space_indent(depth, dtree)

    # Filter tree of structural data (_ccount etc)
    ftree = filter_tree(ngtree)

    # Print all keys at current depth
    # Last one prints special if terminating section
    lastcount = len(ftree.keys())
    for key in sorted(ftree.keys()):
        lastcount = lastcount - 1

        # No structural data
        if not re.search('(^_)|(^Name$)', key):

            # If there are children of current tree, then continue tree.
            # Otherwise terminate tree with └
            if lastcount or len(clist) > 0:
                print("{:}├── {:} : {:}".format(spaces, key, ftree[key]))
            else:
                print("{:}└── {:} : {:}".format(spaces, key, ftree[key]))


    # Close out a section with empty line for visual separation
    if len(clist) > 0 or parent:
        spaces = spaces + "│"
    print(spaces)

    # Print child trees with recursive call to this function
    while len(clist) > 0:

        key = clist.pop(0)

        # Continue printing with depth
        if len(clist) != 0:
            dtree[depth] = 1

        lasttree = False
        # End of indentation, un-indent
        if len(clist) == 0:
            dtree.pop(depth, None)
            lasttree = True

        spaces, indent = get_space_indent(depth, dtree)

        # Indent and print child tree recursively
        if re.search(r'^_child\d+', key):
            cdepth = depth + 4
            print_ngtree(ngtree[key], dtree, depth=cdepth, lasttree=lasttree)

        # Ending section, un-indent
        if len(clist) == 0:
            dtree.pop(depth, None)


def get_space_indent(depth, dtree):
    """Returns indentation and spacing strings for building ngtree output"""

    spaces = ""
    indent = ""
    count = 0

    while count < depth:
        count = count + 1

        if count - 1 in dtree.keys():
            #print("Found Dtree at " + str(count-1))
            spaces = spaces + "│"
        else:
            spaces = spaces + " "
            #iline = "-" + iline
        if count < depth - 4:
            indent = spaces + " "

    indent = indent + "├───"

    return spaces, indent


def filter_tree(ngtree):
    '''Filter structural data'''

    keys = ngtree.keys()
    newtree = dict()

    for key in keys:
        if not re.search('(^_)|(^Name$)', key):
            newtree[key] = ngtree[key]
            #ngtree.pop(key)

    return newtree
