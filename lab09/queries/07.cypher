MATCH (f:Firewall)-[r:PROTECTS]->(:VirtualMachine {id:'vm_01'})
WHERE r.confidence >= 0.9 AND r.validFrom <= date('2026-11-18')
RETURN f.id AS firewall, r.source AS source ORDER BY firewall;
