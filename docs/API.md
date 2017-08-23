# REST API Reference

* Version 2 of the API allows granular querying of the data model via REST Calls
* Most query options support Neo4j/JAVA style regexes
* **Base URL**
  * __`/netgrph/api/v2`__

## Setup
* Configure the [api] section in netgrph.ini
* Enable HTTPS using valid certs for serving API calls beyond localhost
* Setup Process
  * Initialize the SQL Lite database: ```./ctlsrv.py --initdb```
  * Add an API User: ```./ctlsrv --adduser testuser```
  * Run the Server: ```./ctlsrv.py --run```
  * Test a Query: ```curl -u testuser:testpass http://localhost:4096/netgrph/api/v1.1/devs```

# Examples

### Switch path

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

### Networks on a filter (guest VRF with guest access role)

```
curl -u testuser:testpass 'http://localhost:4096/netgrph/api/v1.1/nets?filter=guest:nac-guest'
{
  "Count": 23,
  "Filter": "guest:nac-guest",
  "Name": "Networks",
  "_ccount": 23,
  "_type": "NET",
  "data": [
    {
      "CIDR": "10.29.2.0/23",
      "Description": "None",
      "Gateway": "10.29.2.1",
      "Location": null,
      "Name": "10.29.2.0/23",
      "NetRole": "nac-guest",
      "Router": "mdcmdf",
      "SecurityLevel": "10",
      "StandbyRouter": null,
      "VLAN": "270",
      "VRF": "guest",
      "_type": "CIDR",
      "vrfcidr": "guest-10.29.2.0/23"
    },
```
___

# Device Calls


Device Queries allow you to query the API for all devices, regexes and gather
specific information from individual devices.

* __URLs__
  * __`/devs`__: List all Devices
  * __`/devs/{device}`__: Specific Device
  * __`/devs/{device}/vlans`__: Device VLANs
  * __`/devs/{device}/neighbors`__: Device Neighbors
  * __`/devs/{device}/nets`__: Device Networks

* **Method:**
  * `GET`

* __URL Parameters__
  * __`group`__: Restrict on device group regex
  * __`search`__: Restrict on device name regex
  * __`full`__: Return full device reports (non-truncated and slower)

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
  * __`/nets`__: List of All Networks
  * __`/nets?group=X&cidr=X`__: Networks filtered on group and cidr
  * __`/nets?ip=X`__: Most Specific CIDR from IP

* **Method:**
  * `GET`

* __URL Parameters__
  * __`group`__: Restrict on device group regex
  * __`cidr`__: Restrict on device name regex (optionally replace /24 mask with -24)
  * __`filter`__: Filter via NetGrph vrf:role syntax
  * __`ip`__: Find most specific CIDR for IP

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
  * __`/vlans`__: Retrieve All VLANs
  * __`/vlans/<vlan>`__: Retrieve Specific VLAN in VID or VNAME Format

* __URL Parameters__
  * __`group`__: VLANs in a Management Group
  * __`range`__: VLAN Range eg. 1-1005

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
  * __`/path?src=[ip]&dst=[ip]`__: Universal L2-L4 Path Query
  * __`/spath?src=[switch]&dst[switch.*]`__: Switch paths using a regex
  * __`/rpath?src=[ip]&dst=[ip]&vrf=pci`__: L3 Path inside a VRF
  * __`/fpath?src=[ip]&dst=[ip]`__: L4 Path Query

* __URL Parameters__
  * __`src`__(required): Source of Path Query (regex support on switch paths)
  * __`dst`__(required): Destination of Path Query
  * __`onepath`__(set True): Only show one path, no ECMP
  * __`depth`__: Depth of Graph Search (default 20)
  * __`vrf`__: VRF for Routed Queries
  * __Note__: src and dst support regexes on switch paths

* **Method:**
  * `GET`

* **Success Response:**
  * **Code:** 200 <br />
    **Content:** `{ Name : Report, _type : "PATH" }`

* **Error Response:**
  * **Code:** 401 <br />
    **Content:** `{ message : "Request Error" }`
  
