"""Create the disclosed demo fixture and its equivalent RDF graph."""
import csv
from pathlib import Path

from rdflib import Graph, Literal, Namespace, RDF, XSD

ROOT = Path(__file__).resolve().parent
NS = Namespace("http://example.org/it_infrastructure#")
CLASSES = ("ComputeServer", "Hypervisor", "VirtualMachine", "Firewall", "Sensor", "Incident")
PREFIX = ("srv", "hyp", "vm", "fw", "sensor", "inc")
RELATIONS = {
    "HOSTS_RESOURCE": (0, 1, "hostsResource"),
    "RUNS_VIRTUAL_MACHINE": (1, 2, "runsVirtualMachine"),
    "IS_HOSTED_ON": (2, 1, "isHostedOn"),
    "MONITORS_RESOURCE": (4, 0, "monitorsResource"),
    "PROTECTS": (3, 2, "protects"),
    "AFFECTS": (5, 2, "affects"),
    "DETECTED_BY": (5, 4, "detectedBy"),
    "DEPENDS_ON": (2, 2, "dependsOn"),
}

def node_id(kind, index):
    return f"{PREFIX[kind]}_{index:02d}"

def write_csv(name, columns, rows):
    with (ROOT / "data" / name).open("w", encoding="utf-8", newline="") as out:
        writer = csv.writer(out)
        writer.writerow(columns)
        writer.writerows(rows)

def main():
    graph = Graph()
    graph.bind("it", NS)
    nodes, edges = [], []

    def edge(kind, a, b):
        start, end, predicate = RELATIONS[kind]
        subject, obj = NS[node_id(start, a)], NS[node_id(end, b)]
        nodesource, confidence, valid = "LR09-demo-rule-v1", "1.0", "2026-11-18"
        edges.append((node_id(start, a), node_id(end, b), kind, nodesource, confidence, valid))
        graph.add((subject, NS[predicate], obj))
        statement = NS[f"edge_{len(edges):03d}"]
        for p, o in ((RDF.type, RDF.Statement), (RDF.subject, subject), (RDF.predicate, NS[predicate]),
                     (RDF.object, obj), (NS.source, Literal(nodesource)),
                     (NS.confidence, Literal(confidence, datatype=XSD.double)),
                     (NS.validFrom, Literal(valid, datatype=XSD.date))):
            graph.add((statement, p, o))

    for index in range(1, 21):
        site = f"site_{(index - 1) // 5 + 1}"
        first = (index - 1) // 5 * 5 + 1
        next_index = first + (index - first + 1) % 5
        for kind, label in enumerate(CLASSES):
            key = node_id(kind, index)
            severity = "high" if kind == 5 and index % 2 else "low" if kind == 5 else ""
            nodes.append((key, label, key, site, severity))
            for p, o in ((RDF.type, NS[label]), (NS.id, Literal(key)), (NS.name, Literal(key)),
                         (NS.site, Literal(site))):
                graph.add((NS[key], p, o))
            if severity:
                graph.add((NS[key], NS.severity, Literal(severity)))
        for kind in RELATIONS:
            if kind == "DEPENDS_ON":
                if next_index != first:
                    edge(kind, index, next_index)
            else:
                edge(kind, index, index)
        for kind in ("PROTECTS", "AFFECTS", "MONITORS_RESOURCE"):
            edge(kind, index, next_index)

    assert len(nodes) == 120 and len(edges) == len(set(edges)) == 216
    write_csv("nodes.csv", ("id", "label", "name", "site", "severity"), nodes)
    write_csv("relationships.csv", ("start", "end", "type", "source", "confidence", "validFrom"), edges)
    write_csv("triples_final.csv", ("subject", "predicate", "object"),
              ((a, RELATIONS[kind][2], b) for a, b, kind, *_ in edges))
    graph.serialize(ROOT / "data" / "graph.ttl", format="turtle")

    ddl = [
        "CREATE CONSTRAINT resource_id IF NOT EXISTS FOR (n:Resource) REQUIRE n.id IS UNIQUE",
        "CREATE CONSTRAINT incident_id IF NOT EXISTS FOR (n:Incident) REQUIRE n.id IS UNIQUE",
        "CREATE INDEX resource_site IF NOT EXISTS FOR (n:Resource) ON (n.site)",
        "CREATE INDEX incident_severity IF NOT EXISTS FOR (n:Incident) ON (n.severity)",
    ]
    for label in CLASSES:
        ddl.append(f"""LOAD CSV WITH HEADERS FROM 'file:///nodes.csv' AS row
WITH row WHERE row.label = '{label}'
MERGE (n:Resource {{id: row.id}})
SET n:{label}, n.name = row.name, n.site = row.site, n.severity = nullIf(row.severity, '')""")
    for kind in RELATIONS:
        ddl.append(f"""LOAD CSV WITH HEADERS FROM 'file:///relationships.csv' AS row
WITH row WHERE row.type = '{kind}'
MATCH (a:Resource {{id: row.start}}), (b:Resource {{id: row.end}})
MERGE (a)-[r:{kind}]->(b)
SET r.source = row.source, r.confidence = toFloat(row.confidence), r.validFrom = date(row.validFrom)""")
    (ROOT / "import/01_load.cypher").write_text(";\n\n".join(ddl) + ";\n", encoding="utf-8")

if __name__ == "__main__":
    main()
