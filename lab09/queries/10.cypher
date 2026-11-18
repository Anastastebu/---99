MATCH p = (:VirtualMachine {id:'vm_05'})<-[:DEPENDS_ON*1..4]-(v:VirtualMachine)
RETURN v.id AS affected, min(length(p)) AS depth ORDER BY depth, affected;
