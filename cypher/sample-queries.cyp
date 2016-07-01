--- Switched path between two switches
MATCH (ss:Switch {name:"abc2sw1"}), (ds:Switch {name:"xyz2sw1"}),
  sp = allShortestPaths((ss)-[:NEI*0..5]-(ds)) RETURN sp

-- All downstream neighbors from here
MATCH(s:Switch {name:"core1"})-[e:NEI*0..5]->(rs), (s)-[p:NEI]-(parent) RETURN e,p

-- All networks in the default table
match (v:VRF {name:"default"})<-[e:VRF_IN]-(n:Network) return e

-- Checkout the nglib/query modules
