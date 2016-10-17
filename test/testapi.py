#!/usr/bin/env python3
# Copyright (c) 2016 Jonathan Yantis
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of
# this software and associated documentation files (the "Software"), to deal in
# the Software without restriction, including without limitation the rights to
# use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of
# the Software, and to permit persons to whom the Software is furnished to do so,
# subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS
# FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
# COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER
# IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
# CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#
"""
Test the API Application
"""
import os
import builtins
import re
from base64 import b64encode
import unittest
import tempfile
import time

headers = {
    'Authorization': 'Basic %s' % b64encode(b"testuser:testpass").decode("ascii")
}

# Default Config File Location
config_file = '/etc/netgrph.ini'
alt_config = './docs/netgrph.ini'

# Test/Dev Config
dirname = os.path.dirname(os.path.realpath(__file__))
if re.search(r'\/dev/test$', dirname):
    config_file = './netgrphdev.ini'

# Test configuration exists
if not os.path.exists(config_file):
    if not os.path.exists(alt_config):
        raise Exception("Configuration File not found", config_file)
    else:
        config_file = alt_config

# Import API
builtins.apisrv_CONFIG = config_file
import apisrv

class APITestCase(unittest.TestCase):
    """ API Testing Cases"""
    def setUp(self):
        apisrv.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + tempfile.mkstemp()[1]
        apisrv.app.config['TESTING'] = True
        self.app = apisrv.app.test_client()

        with apisrv.app.app_context():
            apisrv.db.create_all()
            try:
                apisrv.user.add_user("testuser", "testpass")
            except Exception:
                pass

    def tearDown(self):
        apisrv.db.drop_all()
    
    def test_index(self):
        print('Testing Connectivity..')
        rv = self.app.get('/')
        assert b'Authentication required' in rv.data
    
    def test_info(self):
        print('Testing Authentication..')
        rv = self.app.get('/netgrph/api/v1.0/info?test=GETTEST', headers=headers)
        assert b'GET test' in rv.data

    def test_paths(self):
        print("Testing Paths..")
        rv = self.app.get('/netgrph/api/v1.1/path?src=10.26.10.10&dst=10.34.10.10', headers=headers)
        assert b'L4-GW' in rv.data
        assert b'L3-PATH' in rv.data
        assert b'L3-GW' in rv.data

        rv = self.app.get('/netgrph/api/v1.1/spath?dst=mdc.*&src=hvt.*', headers=headers)
        assert b'"distance": 4' in rv.data
    
    def test_vlans(self):
        print("Testing VLANs..")
        rv = self.app.get('/netgrph/api/v1.1/vlans?vrange=250-300', headers=headers)
        assert b'"VLAN ID"' in rv.data
        rv = self.app.get('/netgrph/api/v1.1/vlans/200', headers=headers)
        assert b'"VLAN ID"' in rv.data
    
    def test_nets(self):
        print("Testing Nets..")
        rv = self.app.get('/netgrph/api/v1.1/nets?cidr=10.0.0.0-11', headers=headers)
        assert b'"VLAN"' in rv.data


if __name__ == '__main__':
    unittest.main()
    time.sleep(0.25)
