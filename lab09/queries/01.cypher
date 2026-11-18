MATCH (:ComputeServer {id:'srv_01'})-[:HOSTS_RESOURCE]->(:Hypervisor)-[:RUNS_VIRTUAL_MACHINE]->(v:VirtualMachine)
RETURN v.id AS vm ORDER BY vm;
