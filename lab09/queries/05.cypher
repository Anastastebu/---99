MATCH (v:VirtualMachine {id:'vm_01'})
OPTIONAL MATCH (v)-[:DEPENDS_ON]->(d:VirtualMachine)
RETURN v.id AS vm, d.id AS dependency ORDER BY dependency;
