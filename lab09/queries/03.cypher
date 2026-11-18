MATCH (i:Incident {severity:'high'})-[:AFFECTS]->(:VirtualMachine {id:'vm_02'})
RETURN i.id AS incident ORDER BY incident;
