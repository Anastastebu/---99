MATCH (i:Incident)-[:DETECTED_BY]->(s:Sensor)
WITH s.site AS site, count(DISTINCT i) AS incidents
RETURN site, incidents ORDER BY site;
