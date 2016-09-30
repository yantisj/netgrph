## About

NetGrph was created to serve as a singular network model for automation to
replace the patchwork inherent to our current automation solutions. The API is
developing to provide strong automation capabilities for our network team,
as well as our server, security, and desktop teams.

## Data Model
### Routed SVI Paths from Vlan 110 to 200
![vlan110](https://dl.dropboxusercontent.com/u/73454/svipath2.svg)


[L3 SVIs: Yellow] [L2 VLANs: Green] [Switches/Routers: Blue]
<br>
<br>

### Security Path from Vlan 696 --> 641 across multiple L2/L3 Firewalls
![fwpath](https://dl.dropboxusercontent.com/u/73454/security-path2.svg)


[Networks: Yellow] [VRFs: Green] [Firewalls: Blue]

<br>

### Neighbor Tree from the Core out to a distance of 3

<img src="https://dl.dropboxusercontent.com/u/73454/network-graph.svg" alt="NEI Tree" width="800" height="800">



<br>

## Performance

On our network containing 700+ routers/switches, 2000+ SVIs and 10,000+ VLAN to
switch mappings, performance on almost all netgrph queries is below 150ms. Full
ngreport queries can take longer, but it's for creating network-wide reports.

The database update time on our localhost server with SSDs is 150sec for a
complete network refresh. When importing to an unoptimized VM on a remote
server, the import time is 5min. The network import speed could be dramatically
increased if rewritten using the Bolt driver, which is planned.

## Dependencies

NetGrph is a Python3.4+ application, but could be back-ported to Python2.7
fairly easily. It relies on both the py2neo and neo4j bolt driver (install via
pip3). The plan is to eventually convert all driver code to the bolt driver as
it matures.

NetGrph requires [CSV files](test/csv/) with all of your Switches/Routers, Networks,
VLANs, and CDP/LLDP Neighbors in order to be multi-vendor compatible. I provide
IOS and NXOS configuration parsers, as well as a sample network topology to play
with. For Cisco-based networks, a generic CDP/LLDP mapper is all that's missing.
NetGrph is compatible with NetDB Neighbor Data:
(https://sourceforge.net/projects/netdbtracking/). Once stable, I'll package a
bundled NetDB OVA with NetGrph included.

If anyone has a dependable LLDP/CDP walker they recommend (I'm sure there are
many), please contact me. This only needs src_switch,src_port,dst_switch,dst_port.
I have tested a few different open-source packages, but have yet to find a suitable
tool that is reliable enough.

NetGrph was developed on Ubuntu 14.04 LTS, tested on 16.04, and should be
compatible with other versions of linux. I highly recommend using Ubuntu at this
early stage for better support. I also plan to create an ansible build script in
the next few months. It also works just find on MacOS but there are no Ansible or
install instructions for that OS.

## Planned Features

* Add configuration snippets for each hop on traverals
* Import all Network ACL's for L4 analysis
* Improve NetDB integration with universal search
* Implement Dijkstra's Algorithm for cost-based path traversals (database plugin)
* Simple Web Interface for Path Traversals and report generation
* Statseeker integration for including graphs/errors in reports

## Future

I am open to expanding NetGrph for the needs of MPLS networks and other
network/security domains where appropriate. The application was written to be
generic and approachable for use with both SDN and existing networks.

I have also added some lightweight integration with my existing [NetDB
application](http://netdbtracking.sourceforge.net), but that will be both
focused and optional. If you manage to create any new parsers or integrate with
other vendor APIs, please contribute your code back.

I would like to add a GUI, but at this time I'm focussed on using the
application to automate tasks. In theory, it should be easy to create [D3
visualizations](https://github.com/d3/d3/wiki/Gallery) from the NGTree
data-structures. If anyone manages to create a simple GUI or use this
application to create some interesting visualizations, I'd be happy to help and
would love to see the results.

I will not be expanding the application to be a full-blown NMS, since there are
many tools that accomplish this. If you manage to expand the core modeling
functionality and think it should be included in the main codebase, I'd like to
consider including it here.

See the [CONTRIBUTING](CONTRIBUTING.md) document for more information.

## Support

You can open an issue via GitHub, or if you would like to speak with me
directly, I monitor the #netgrph channel the [networktocode slack
group](https://networktocode.herokuapp.com/). Please try and contact me there
for any interactive support.

## Contributions

Please see the [Contributions](CONTRIBUTING.md) document in docs for
information about how you can contribute back to NetGrph.

## Contributors
* Jonathan Yantis ([yantisj](https://github.com/yantisj))

## License
NetGrph is licensed under the GNU AGPLv3 License.
