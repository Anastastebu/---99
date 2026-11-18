MATCH p = (:VirtualMachine {id:'vm_01'})-[:DEPENDS_ON*1..4]->(d:VirtualMachine)
RETURN d.id AS dependency, min(length(p)) AS depth ORDER BY depth, dependency;
