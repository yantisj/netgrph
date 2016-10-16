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

___

## Examples

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

# Device Queries

Device Queries allow you to query the API for all devices, regexes and gather
specific information from individual devices.

#### Get Options

* __group__: Restrict on device group regex
* __search__: Restrict on device name regex
* __full__: Return full device reports (non-truncated and slower)

#### URIs

* __/devs__ - list of all devices
* __/devs/{device}__ - specific device
* __/devs/{device}/vlans__ - device vlans
* __/devs/{device}/neighbors__ - device neighbors
* __/devs/{device}/nets__ - device networks
* __/devs?search='.*'__ - search on devices via regex
* __/devs?group='.*'__ - search on management group via regex
* __/devs?full=1__ - get full device reports

# Network Queries

Network Queries allow you to query for networks based on CIDRs, VRF, Role and
Group filters.

#### GET Options

* __group__: Restrict on device group regex
* __cidr__: Restrict on device name regex
* __filter__: Filter via NetGrph vrf:role syntax
* __ip__: Find most specific CIDR for IP

#### URIs
* __/nets__ - List of all networks
* __/nets?group=X__ - List of all networks in a management group
* __/nets?cidr=X__ - List of all networks found in a CIDR
* __/nets?ip=X__ - Most Specific CIDR Match

# VLAN Queries

VLAN Queries return lists of all VLANs, specific VLAN trees and VLANs for groups

#### GET Options
* __group__: VLANs in a Management Group
* __vid__: VLAN ID
* __vname__: MGMT-VID Format
* __range__: VLAN Range eg. 1-1005

#### URIs

* /vlans
* /vlans?vid=X
* /vlans?vname=X
* /vlans?group=X


# Path Queries

Path queries allow you to do L2-L4 traversals between any two points on the network.

#### GET Options

* __src__(required): Source of Path Query (regex support on switch paths)
* __dst__(required): Destination of Path Query
* __onepath__(set True): Only show one path, no ECMP
* __depth__: Depth of Graph Search (default 20)
* __vrf__: VRF for Routed Queries

Note: src and dst support regexes on switch paths

#### URIs
* /path?src=[ip]&dst=[ip] - Universal L2-L4 Path Query
* /spath?src=[switch]&dst[switch.*] - Switch paths using a regex
* /rpath?src=[ip]&dst=[ip]&vrf=pci - L3 Path inside a VRF
* /fpath?src=[ip]&dst=[ip] - L4 Path Query
