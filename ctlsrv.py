#!/usr/bin/env python3
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
"""
Manage the API Server
"""
import builtins
import os
import re
import getpass
import argparse

parser = argparse.ArgumentParser()

parser = argparse.ArgumentParser(prog='ctlsrv.py',
                                 description='Manage the API Server')

parser.add_argument("--adduser", metavar="user", help="Add API User to DB", type=str)
parser.add_argument("--newpass", metavar="user", help="Update Password", type=str)
parser.add_argument("--testuser", metavar="user", help="Test Authentication", type=str)
parser.add_argument("--deluser", metavar="user", help="Delete API User", type=str)
parser.add_argument("--initdb", help="Initialize the Database", action="store_true")
parser.add_argument("--debug", help="Set debugging level", type=int)
parser.add_argument("-v", help="Verbose Output", action="store_true")

args = parser.parse_args()


# Default Config File Location
config_file = '/etc/netgrph.ini'
alt_config = './docs/netgrph.ini'

# Test/Dev Config
dirname = os.path.dirname(os.path.realpath(__file__))
if re.search(r'\/dev$', dirname):
    config_file = 'netgrphdev.ini'
elif re.search(r'\/test$', dirname):
    config_file = "netgrphdev.ini"

# Test configuration exists
if not os.path.exists(config_file):
    if not os.path.exists(alt_config):
        raise Exception("Configuration File not found", config_file)
    else:
        config_file = alt_config

# Import API
builtins.apisrv_CONFIG = config_file
import apisrv

verbose = 0
if args.v:
    verbose = 1
if args.debug:
    verbose = args.debug

# Initialize the Database
if args.initdb:
    apisrv.db.create_all()
    apisrv.db.session.commit()

# Add user to DB
elif args.adduser:

    passwd = getpass.getpass('Password:')
    verify = getpass.getpass('Verify Password:')

    if passwd == verify:
        phash = apisrv.user.add_user(args.adduser, passwd)
        if phash:
            print("Successfully Added User to Database")
        else:
            print("Error: Could not Add User to Database")
    else:
        print("Error: Passwords do not match")
    
# Update User Password
elif args.newpass:
    passwd = getpass.getpass('New Password:')
    verify = getpass.getpass('Verify Password:')

    if passwd == verify:
        phash = apisrv.user.update_password(args.newpass, passwd)
        if phash:
            print("Successfully Updated Password")
        else:
            print("Error: Could not Update Password")
    else:
        print("Error: Passwords do not match")

# Delete a User
elif args.deluser:
    ucheck = apisrv.user.del_user(args.deluser)

    if ucheck:
        print("Successfully Deleted User")
    else:
        print("Username not found in DB")

# Test Authentication
elif args.testuser:
    passwd = getpass.getpass('Password:')
    phash = apisrv.user.authenticate_user(args.testuser, passwd)
    if phash:
        print("Successfully Authenticated")
    else:
        print("Authentication Failed")
else:
    parser.print_help()
    print()