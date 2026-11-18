MATCH (a:VirtualMachine {id:'vm_01'}), (b:VirtualMachine {id:'vm_05'})
MATCH p = shortestPath((a)-[:DEPENDS_ON*..6]->(b))
RETURN [n IN nodes(p) | n.id] AS route, length(p) AS hops;
