CREATE CONSTRAINT resource_id IF NOT EXISTS FOR (n:Resource) REQUIRE n.id IS UNIQUE;

CREATE CONSTRAINT incident_id IF NOT EXISTS FOR (n:Incident) REQUIRE n.id IS UNIQUE;

CREATE INDEX resource_site IF NOT EXISTS FOR (n:Resource) ON (n.site);

CREATE INDEX incident_severity IF NOT EXISTS FOR (n:Incident) ON (n.severity);

LOAD CSV WITH HEADERS FROM 'file:///nodes.csv' AS row
WITH row WHERE row.label = 'ComputeServer'
MERGE (n:Resource {id: row.id})
SET n:ComputeServer, n.name = row.name, n.site = row.site, n.severity = nullIf(row.severity, '');

LOAD CSV WITH HEADERS FROM 'file:///nodes.csv' AS row
WITH row WHERE row.label = 'Hypervisor'
MERGE (n:Resource {id: row.id})
SET n:Hypervisor, n.name = row.name, n.site = row.site, n.severity = nullIf(row.severity, '');

LOAD CSV WITH HEADERS FROM 'file:///nodes.csv' AS row
WITH row WHERE row.label = 'VirtualMachine'
MERGE (n:Resource {id: row.id})
SET n:VirtualMachine, n.name = row.name, n.site = row.site, n.severity = nullIf(row.severity, '');

LOAD CSV WITH HEADERS FROM 'file:///nodes.csv' AS row
WITH row WHERE row.label = 'Firewall'
MERGE (n:Resource {id: row.id})
SET n:Firewall, n.name = row.name, n.site = row.site, n.severity = nullIf(row.severity, '');

LOAD CSV WITH HEADERS FROM 'file:///nodes.csv' AS row
WITH row WHERE row.label = 'Sensor'
MERGE (n:Resource {id: row.id})
SET n:Sensor, n.name = row.name, n.site = row.site, n.severity = nullIf(row.severity, '');

LOAD CSV WITH HEADERS FROM 'file:///nodes.csv' AS row
WITH row WHERE row.label = 'Incident'
MERGE (n:Resource {id: row.id})
SET n:Incident, n.name = row.name, n.site = row.site, n.severity = nullIf(row.severity, '');

LOAD CSV WITH HEADERS FROM 'file:///relationships.csv' AS row
WITH row WHERE row.type = 'HOSTS_RESOURCE'
MATCH (a:Resource {id: row.start}), (b:Resource {id: row.end})
MERGE (a)-[r:HOSTS_RESOURCE]->(b)
SET r.source = row.source, r.confidence = toFloat(row.confidence), r.validFrom = date(row.validFrom);

LOAD CSV WITH HEADERS FROM 'file:///relationships.csv' AS row
WITH row WHERE row.type = 'RUNS_VIRTUAL_MACHINE'
MATCH (a:Resource {id: row.start}), (b:Resource {id: row.end})
MERGE (a)-[r:RUNS_VIRTUAL_MACHINE]->(b)
SET r.source = row.source, r.confidence = toFloat(row.confidence), r.validFrom = date(row.validFrom);

LOAD CSV WITH HEADERS FROM 'file:///relationships.csv' AS row
WITH row WHERE row.type = 'IS_HOSTED_ON'
MATCH (a:Resource {id: row.start}), (b:Resource {id: row.end})
MERGE (a)-[r:IS_HOSTED_ON]->(b)
SET r.source = row.source, r.confidence = toFloat(row.confidence), r.validFrom = date(row.validFrom);

LOAD CSV WITH HEADERS FROM 'file:///relationships.csv' AS row
WITH row WHERE row.type = 'MONITORS_RESOURCE'
MATCH (a:Resource {id: row.start}), (b:Resource {id: row.end})
MERGE (a)-[r:MONITORS_RESOURCE]->(b)
SET r.source = row.source, r.confidence = toFloat(row.confidence), r.validFrom = date(row.validFrom);

LOAD CSV WITH HEADERS FROM 'file:///relationships.csv' AS row
WITH row WHERE row.type = 'PROTECTS'
MATCH (a:Resource {id: row.start}), (b:Resource {id: row.end})
MERGE (a)-[r:PROTECTS]->(b)
SET r.source = row.source, r.confidence = toFloat(row.confidence), r.validFrom = date(row.validFrom);

LOAD CSV WITH HEADERS FROM 'file:///relationships.csv' AS row
WITH row WHERE row.type = 'AFFECTS'
MATCH (a:Resource {id: row.start}), (b:Resource {id: row.end})
MERGE (a)-[r:AFFECTS]->(b)
SET r.source = row.source, r.confidence = toFloat(row.confidence), r.validFrom = date(row.validFrom);

LOAD CSV WITH HEADERS FROM 'file:///relationships.csv' AS row
WITH row WHERE row.type = 'DETECTED_BY'
MATCH (a:Resource {id: row.start}), (b:Resource {id: row.end})
MERGE (a)-[r:DETECTED_BY]->(b)
SET r.source = row.source, r.confidence = toFloat(row.confidence), r.validFrom = date(row.validFrom);

LOAD CSV WITH HEADERS FROM 'file:///relationships.csv' AS row
WITH row WHERE row.type = 'DEPENDS_ON'
MATCH (a:Resource {id: row.start}), (b:Resource {id: row.end})
MERGE (a)-[r:DEPENDS_ON]->(b)
SET r.source = row.source, r.confidence = toFloat(row.confidence), r.validFrom = date(row.validFrom);
