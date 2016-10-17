# API Documentation

* The API is currently under development and in flux.
* Base URL: /netgrph/api/v1.1

## Setup
* Configure the [api] section in netgrph.ini
* Enable HTTPS with valid certs for listening beyond localhost
* Initialize the SQL Lite database: ```./ctlsrv.py --initdb```
* Add an API User: ```./ctlsrv --adduser testuser```
* Run the Server: ```./ctlsrv.py --run```
* Test a Query: ```curl -u testuser:testpass http://localhost:4096/netgrph/api/v1.1/devs```

# Examples

* Switch path

  ```
  $ curl -u testuser:testpass 'http://localhost:4096/netgrph/api/v1.0/spath?src=mdcmdf&dst=core1'
  {
    "Distance": 1,
    "Links": 1,
    "Name": "mdcmdf -> core1",
    "Search Depth": "20",
    "Traversal Type": "All Paths",
    "_ccount": 1,
    "_type": "L2-PATH",
    "data": [
      {
        "From Channel": "0",
        "From Model": "WS-C3850-48U",
        "From Port": "Te1/1/4",
        "From Switch": "mdcmdf",
        "Link VLANs": "1246,2200,2314,2320,2324,2365,2376",
        "Link rVLANs": "1246,2200,2314,2320,2324,2365,2376",
        "Name": "#1 mdcmdf(Te1/1/4) -> core1(Eth10/21)",
        "Native VLAN": "2200",
        "To Channel": "0",
        "To Model": "Nexus7000 C7010",
        "To Port": "Eth10/21",
        "To Switch": "core1",
        "_ccount": 0,
        "_cversion": "03.06.04.E RELEASE SOFTWARE (fc2)",
        "_pversion": "Version 6.2(16)",
        "_reverse": 1,
        "_rvlans": "1246,2200,2314,2320,2324,2365,2376",
        "_type": "L2-HOP",
        "data": [],
        "distance": 1
      }
    ]
  }
  ```
___

# Device Calls


Device Queries allow you to query the API for all devices, regexes and gather
specific information from individual devices.

* __URLs__
  * List all Devices
    * __/devs__
  * Specific Device
    * __/devs/{device}__
  * Device VLANs
    * __/devs/{device}/vlans__
  * Device Neighbors
    * __/devs/{device}/neighbors__
  * Device Networks
    * __/devs/{device}/nets__

* **Method:**
  * `GET`

* __URL Parameters__
  * __group__: Restrict on device group regex
  * __search__: Restrict on device name regex
  * __full__: Return full device reports (non-truncated and slower)

* **Success Response:**
  * **Code:** 200 <br />
    **Content:** `{ Name : Report, _type : "VIDs" }`

* **Error Response:**
  * **Code:** 401 <br />
    **Content:** `{ message : "Request Error" }`

___

# Network Calls

Network Queries allow you to query for networks based on CIDRs, VRF, Role and
Group filters.

* __URLs__
  * `__/nets__`: List of All Networks
  * `__/nets?group=X&cidr=X__`: Networks filtered on group and cidr
  * `__/nets?ip=X__`: Most Specific CIDR from IP

* **Method:**
  * `GET`

* __URL Parameters__
  * __group__: Restrict on device group regex
  * __cidr__: Restrict on device name regex (optionally replace /24 mask with -24)
  * __filter__: Filter via NetGrph vrf:role syntax
  * __ip__: Find most specific CIDR for IP

* **Success Response:**
  * **Code:** 200 <br />
    **Content:** `{ Name : Report, _type : "Networks" }`

* **Error Response:**
  * **Code:** 401 <br />
    **Content:** `{ message : "Request Error" }`

___

# VLAN Calls

VLAN Queries return lists of all VLANs, specific VLAN trees and VLANs for groups

* __URLs__
  * /vlans
  * /vlans?vid=X
  * /vlans?vname=X
  * /vlans?group=X

* __URL Parameters__
  * __group__: VLANs in a Management Group
  * __vid__: VLAN ID
  * __vname__: MGMT-VID Format
  * __range__: VLAN Range eg. 1-1005

* **Success Response:**
  * **Code:** 200 <br />
    **Content:** `{ Name : Report, _type : "VLANs" }`

* **Error Response:**
  * **Code:** 401 <br />
    **Content:** `{ message : "Request Error" }`

___

# Path Calls

Path queries allow you to do L2-L4 traversals between any two points on the network.

* __URLs__
  * Universal L2-L4 Path Query
    * `/path?src=[ip]&dst=[ip]`
  * Switch paths using a regex
    * `/spath?src=[switch]&dst[switch.*]`
  * L3 Path inside a VRF
    * `/rpath?src=[ip]&dst=[ip]&vrf=pci`
  * L4 Path Query
    * `/fpath?src=[ip]&dst=[ip]`

* __URL Parameters__
  * __src__(required): Source of Path Query (regex support on switch paths)
  * __dst__(required): Destination of Path Query
  * __onepath__(set True): Only show one path, no ECMP
  * __depth__: Depth of Graph Search (default 20)
  * __vrf__: VRF for Routed Queries
  * `Note:` src and dst support regexes on switch paths

* **Method:**
  * `GET`

* **Success Response:**
  * **Code:** 200 <br />
    **Content:** `{ Name : Report, _type : "PATH" }`

* **Error Response:**
  * **Code:** 401 <br />
    **Content:** `{ message : "Request Error" }`
  
