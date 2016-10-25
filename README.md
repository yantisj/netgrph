## Synopsis

NetGrph is an abstract network model for automation, providing a unified network
view across diverse network components in order to manage them as a single
system via the [Neo4j Graph Database](http://neo4j.com). This enables you to
navigate your traditional LAN/WAN and/or mixed SDN networks as interconnected
nodes and relationships in software, all modeled via the network configurations
as they exist rather than secondary sources.

NetGrph can perform universal L2/L3/L4 path traversals, providing context for
each layer along the path. It also serves as a VLAN and CIDR database, showing
how everything is related. It scales well on even the largest networks,
allowing sub-second queries across thousands of network devices. This enables
the mapping of complex network relationships for discovery and automation.

Data from queries can be returned as CSV, JSON, YAML, or Ascii tree-art. Network
Visualizations can be created by querying the Neo4j webapp as shown below. The
data model should translate for use with tools such as D3.js, vis.js or Graphwiz
via both the native Neo4j API as well as NetGrph's tree data structure.

All data is accessible via an API, and the lightweight netgrph client can be
distributed to multiple machines.

## Graph Data Model Example: Vlan 110 -> 200 Traversal
![vlan110](https://dl.dropboxusercontent.com/u/73454/svipath2.svg)


[L3 SVIs: Yellow] [L2 VLANs: Green] [Switches/Routers: Blue]
<br>
<br>

## Features
* Universal Layer2 - Layer4 pathfinding between any two network devices (Full L2 path completion requires NetDB)
* Path Queries can return a single path, or all ECMPs
* L3 Network Database of all networks (Automated, VRF aware, and searchable)
* Search for networks via CIDR or VRF/Role based filters (eg. perim:printers|thinclient, all printers and thin clients in the perim VRF)
* VLAN Inventory of all VLAN instances across the network, segmented by switch domain
* Maps L2 VLAN bridges across switch domains, and calculates local/global STP roots
* Maps L2 paths between devices (regexs supported, eg. dc.* -> dc.* for all datacenter links)
* Reports both the configured VLANs and actual VLANs existing on each link for all L2 paths
* Optional Secure REST API Server and Client
* High performance, low latency queries (All queries are sub-second)
* Easily extendable to support mixed-vendor environnments via configuration parsing to CSV input format
* Ansible playbooks for a five minute install on Ubuntu 14.04/16.04

## Requirements
* Python 3.4+ (recommend running via virtualenv)
* Ubuntu or MacOS (should run on any Python compatible platform, but I only support these)
* [Neo4j Graph Database](https://neo4j.com) and Java8
* For Cisco devices, must provide stored configurations (See [Rancid](http://www.shrubbery.net/rancid/) / [Oxidized](https://github.com/ytti/oxidized))
* Requires CDP/LLDP Discovery Data via [NetDB](http://netdbtracking.sourceforge.net) or [NetCrawl](https://github.com/ytti/netcrawl)
* Third-party network devices need to be parsed into the [NetGrph CSV format](test/csv/)
* Please send me any parsers you create

## Documentation

* [NetGrph Read The Docs](http://netgrph.readthedocs.io/)

## Path Traversal Example
```
$ ./netgrph.py -p 10.26.72.142 10.34.72.24

┌─[ PATHs L2-L4 ]
│
├── L2 Path : abc7t1sw1 (Gi2/42) -> abc7t1sw1 (Gi1/38)
├── L3 Path : 10.26.72.0/22 -> 10.34.72.0/22
├── L4 Path : VRF:default -> FwutilFW -> VRF:utility
├── Lx Path : 10.26.72.142 -> 10.34.72.24
├── Traversal Type : All Paths
│
├─────[ SRC 10.26.72.142 04bd.88cb.xxxx abc7t1sw1(Gi2/42) [vid:260] ]
│
├───┬─[ L2-PATH abc7t1sw1 -> abcmdf1|abcmdf2 ]
│   │
│   ├─────[ L2-HOP #1 abc7t1sw1(Te5/1) -> abcmdf1(Eth1/8) [pc:1->108] ]
│   │
│   └─────[ L2-HOP #1 abc7t1sw1(Te6/1) -> abcmdf2(Eth1/8) [pc:1->108] ]
│
├─────[ L3GW 10.26.72.0/22 abcmdf1|abcmdf2 ]
│
├───┬─[ L3-PATH 10.26.72.0/22 -> 10.25.11.0/24 ]
│   │
│   ├───┬─[ L3-HOP #1 abcmdf1(10.23.74.11) -> core1(10.23.74.10) [vid:2074] ]
│   │   │
│   │   └─────[ L2-HOP #1 abcmdf1(Eth2/26) -> core1(Eth7/27) ]
│   │
│   ├───┬─[ L3-HOP #1 abcmdf1(10.23.74.21) -> core2(10.23.74.20) [vid:3074] ]
│   │   │
│   │   └─────[ L2-HOP #1 abcmdf1(Eth3/8) -> core2(Eth4/25) ]
│   │
│   ├───┬─[ L3-HOP #1 abcmdf2(10.23.78.11) -> core1(10.23.78.10) [vid:2078] ]
│   │   │
│   │   └─────[ L2-HOP #1 abcmdf2(Eth2/26) -> core1(Eth8/25) ]
│   │
│   └───┬─[ L3-HOP #1 abcmdf2(10.23.78.21) -> core2(10.23.78.20) [vid:3078] ]
│       │
│       └─────[ L2-HOP #1 abcmdf2(Eth3/8) -> core2(Eth8/25) ]
│
├─────[ L4GW 10.25.11.0/24 [rtr: vid:1601 vrf:default] ]
│
├─────[ L4FW FwutilFW ]
│
├─────[ L4GW 10.25.12.0/24 [rtr: vid:1602 vrf:utility] ]
│
├───┬─[ L3-PATH 10.25.12.0/24 -> 10.34.72.0/22 ]
│   │
│   ├───┬─[ L3-HOP #1 core1(10.23.74.10) -> abcmdf1(10.23.74.11) [vid:2461] ]
│   │   │
│   │   └─────[ L2-HOP #1 core1(Eth7/27) -> abcmdf1(Eth2/26) ]
│   │
│   ├───┬─[ L3-HOP #1 core1(10.23.78.10) -> abcmdf2(10.23.78.11) [vid:2462] ]
│   │   │
│   │   └─────[ L2-HOP #1 core1(Eth8/25) -> abcmdf2(Eth2/26) ]
│   │
│   ├───┬─[ L3-HOP #1 core2(10.23.74.20) -> abcmdf1(10.23.74.21) [vid:3461] ]
│   │   │
│   │   └─────[ L2-HOP #1 core2(Eth4/25) -> abcmdf1(Eth3/8) ]
│   │
│   └───┬─[ L3-HOP #1 core2(10.23.78.20) -> abcmdf2(10.23.78.21) [vid:3462] ]
│       │
│       └─────[ L2-HOP #1 core2(Eth8/25) -> abcmdf2(Eth3/8) ]
│
├─────[ L3GW 10.34.72.0/22 abcmdf1|abcmdf2 ]
│
├───┬─[ L2-PATH abcmdf1|abcmdf2 -> abc7t1sw1 ]
│   │
│   ├─────[ L2-HOP #1 abcmdf1(Eth1/8) -> abc7t1sw1(Te5/1) [pc:108->1] ]
│   │
│   └─────[ L2-HOP #1 abcmdf2(Eth1/8) -> abc7t1sw1(Te6/1) [pc:108->1] ]
│
└─────[ DST 10.34.72.24 000a.b004.xxxx abc7t1sw1(Gi1/38) [vid:340] ]
```

## Installation

See the [Install Instructions](docs/INSTALL.md)

## Support

See refer to the documentation first: [NetGrph Read The
Docs](http://netgrph.readthedocs.io/)

You can open an issue via GitHub, or if you would like to speak with me
directly, I monitor the #netgrph channel the [networktocode slack
group](https://networktocode.herokuapp.com/). Please try and contact me there
for any interactive support.

## Contributions

Please see the [Contributions](docs/CONTRIBUTING.md) document in docs for
information about how you can contribute back to NetGrph.

## Contributors
* Jonathan Yantis ([yantisj](https://github.com/yantisj))

## License
NetGrph is licensed under the GNU AGPLv3 License.
