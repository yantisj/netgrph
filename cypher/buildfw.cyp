--
-- Manual Cypher Topology Commands
-- Will not be purged by cache since they're missing a timestamp
--
-- Create a Default network and link it to the outside VRF
MERGE (n:Network {vrfcidr:"outside-0.0.0.0/0"}) SET n += {name:"outside", cidr:"0.0.0.0/0", vid:'0', desc:"Default Route", vrf:"outside", gateway:"0.0.0.0"}
MATCH (n:Network {cidr:"0.0.0.0/0"}), (v:VRF {name:"outside"}) MERGE (n)-[e:VRF_IN]->(v)
MATCH (s:Switch {name:"ExternalFW"}), (n:Network {vrfcidr:"outside-0.0.0.0/0"}) MERGE (n)-[e:ROUTED_BY {vrf:"OUTSIDE"}]->(s)

-- Create a SWITCHED_FW and insert it between two networks on different VRFs
MERGE (fw:Switch:FW {name:'ExternalFW', type:"PaloAlto", hostname:"pa-fw-l2fw.domain.com", logIndex:"fwlogs"});
MATCH (fw:Switch:FW {name:'ExternalFW'}), (n:Network {vid:"1095"}) MERGE (n)-[e:SWITCHED_FW]->(fw)
MATCH (fw:Switch:FW {name:'ExternalFW'}), (n:Network {vid:"1099"}) MERGE (n)-[e:SWITCHED_FW]->(fw)
