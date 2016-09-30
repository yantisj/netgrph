# Welcome to the NetGrph Documentation

NetGrph is designed to be a platform for automation, providing a unified network
model across diverse network components in order to manage them as a single
system by leveraging the Neo4j Graph Database](http://neo4j.com). This enables
you to navigate your traditional LAN/WAN and/or mixed SDN networks as
interconnected nodes and relationships in software, and is being shared to help
others with network discovery, and automation.

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

## Supported Devices

NetGrph is designed to support all network vendors, but currently only has
scrapers available for Cisco IOS and NXOS devices. Adding support for other
devices should be relatively trivial.

## About NetGrph

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

Find out more [About NetGrph](About.md)

# Documentation Guide

### Installation

See the [Installation Guide](INSTALL.md)

Ansible Instructions are located [Here](playbooks/README.md)

### Tutorials

See the [Tutorials Documentation](Tutorials.md)

### Command Line Interface

See the [Command Line Interface Documentation](CLI.md)

### API Documentation

See the [API Documentation](API.md)

