MATCH (s:Sensor)-[:MONITORS_RESOURCE]->(:ComputeServer {id:'srv_01'})
RETURN s.id AS sensor ORDER BY sensor;
