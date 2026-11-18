"""Execute LR09 and write measured evidence. Use a dedicated lab database."""
import argparse
import getpass
import json
import os
from pathlib import Path
import re
import secrets
from time import perf_counter

from neo4j import GraphDatabase, Query
from neo4j.exceptions import Neo4jError
from rdflib import Graph

ROOT = Path(__file__).resolve().parent

def save(name, values):
    path = ROOT / "results" / name
    path.write_text(json.dumps(values, ensure_ascii=False, indent=2, default=str) + "\n", encoding="utf-8")

def read(path):
    return (ROOT / path).read_text(encoding="utf-8").strip().removesuffix(";")

def reference_query(index):
    return read(f"queries/{index:02}.cypher")

def measure(driver, cypher):
    started = perf_counter()
    rows, summary, _ = driver.execute_query(Query(cypher, timeout=15), database_="neo4j")
    return [row.data() for row in rows], (perf_counter() - started) * 1000, summary

def counts(run):
    return run("MATCH (n:Resource) RETURN count(n) AS nodes")[0] | run(
        "MATCH (:Resource)-[r]->(:Resource) RETURN count(r) AS relationships")[0]

def import_graph(run):
    versions = run("CALL dbms.components() YIELD name, versions, edition RETURN name, versions, edition")
    script = read("import/01_load.cypher").split(";")
    for statement in script:
        run(statement)
    first = counts(run)
    for statement in script:
        run(statement)
    second = counts(run)
    assert first == second == {"nodes": 120, "relationships": 216}, (first, second)
    try:
        run("CREATE (:Resource {id:'srv_01'})")
    except Neo4jError as error:
        if error.code != "Neo.ClientError.Schema.ConstraintValidationFailed":
            raise
        violation = {"code": error.code, "message": error.message}
    else:
        raise AssertionError("Expected an id constraint violation")
    run("CALL db.awaitIndexes(60)")
    constraints = run("SHOW CONSTRAINTS YIELD name, type RETURN name, type ORDER BY name")
    indexes = run("SHOW INDEXES YIELD name, type, state, owningConstraint "
                  "RETURN name, type, state, owningConstraint ORDER BY name")
    save("import.json", dict(versions=versions, first=first, second=second, violation=violation,
                             constraints=constraints, indexes=indexes))
    print(f"Import OK: {first}", flush=True)

def graph_analysis(run, driver):
    version = run("RETURN gds.version() AS version")
    run("CALL gds.graph.drop('lab09_topology', false) YIELD graphName RETURN graphName")
    projection = run("""CALL gds.graph.project('lab09_topology', 'Resource', {
      HOSTS_RESOURCE:{orientation:'UNDIRECTED'}, RUNS_VIRTUAL_MACHINE:{orientation:'UNDIRECTED'},
      MONITORS_RESOURCE:{orientation:'UNDIRECTED'}, PROTECTS:{orientation:'UNDIRECTED'},
      AFFECTS:{orientation:'UNDIRECTED'}, DETECTED_BY:{orientation:'UNDIRECTED'},
      DEPENDS_ON:{orientation:'UNDIRECTED'}})
      YIELD graphName, nodeCount, relationshipCount RETURN graphName, nodeCount, relationshipCount""")
    rank = run("""CALL gds.pageRank.write('lab09_topology', {writeProperty:'pagerank', concurrency:1,
                   maxIterations:200, dampingFactor:0.85, tolerance:0.0000001})
                   YIELD nodePropertiesWritten, ranIterations, didConverge
                   RETURN nodePropertiesWritten, ranIterations, didConverge""")
    louvain = run("""CALL gds.louvain.write('lab09_topology', {writeProperty:'community',
                      concurrency:1, maxLevels:10, tolerance:0.0001})
                      YIELD communityCount, modularity, nodePropertiesWritten
                      RETURN communityCount, modularity, nodePropertiesWritten""")
    top = run("MATCH (n:Resource) RETURN n.id AS id, n.site AS site, "
              "n.pagerank AS pagerank ORDER BY pagerank DESC, id LIMIT 10")
    groups = run("MATCH (n:Resource) RETURN n.community AS community, count(*) AS nodes, "
                 "collect(DISTINCT n.site) AS sites ORDER BY nodes DESC, community")
    written = run("MATCH (n:Resource) RETURN count(n.pagerank) AS pagerank, count(n.community) AS community")[0]
    assert rank[0]["didConverge"] and len(top) == 10 and len(groups) >= 3 and written == {"pagerank":120, "community":120}
    save("gds.json", dict(version=version, projection=projection, rank=rank, louvain=louvain,
                          top=top, groups=groups, written=written))
    run("CALL gds.graph.drop('lab09_topology') YIELD graphName RETURN graphName")
    profiles = {}
    for key, cypher in {
        "before": "MATCH (n:Resource) USING SCAN n:Resource WHERE n.site='site_1' RETURN count(n) AS total",
        "after": "MATCH (n:Resource) USING INDEX n:Resource(site) WHERE n.site='site_1' RETURN count(n) AS total",
        "shortest_path": reference_query(6),
    }.items():
        rows, _, summary = measure(driver, "PROFILE " + cypher)
        def sum_hits(plan):
            return plan.get("dbHits", 0) + sum(sum_hits(p) for p in plan.get("children", []))
        profiles[key] = dict(query=cypher, result=rows, db_hits=sum_hits(summary.profile),
                             profile=summary.profile)
    assert profiles["before"]["result"] == profiles["after"]["result"]
    save("profile.json", profiles)
    print("GDS and PROFILE OK", flush=True)

def compare(driver):
    graph = Graph().parse(ROOT / "data/graph.ttl")
    reference = {}
    comparisons = []
    for index in range(1, 11):
        cypher = reference_query(index)
        expected, _, _ = measure(driver, cypher)
        reference[index] = expected
        if index > 5:
            continue
        sparql = read(f"sparql/{index:02}.rq")
        graph.query(sparql)
        cypher_ms, sparql_ms = [], []
        for _ in range(5):
            _, elapsed, _ = measure(driver, cypher)
            cypher_ms.append(elapsed)
            started = perf_counter()
            rdf_rows = [{key: value.toPython() for key, value in row.asdict().items()}
                        for row in graph.query(sparql)]
            sparql_ms.append((perf_counter() - started) * 1000)
        assert expected == rdf_rows, (index, expected, rdf_rows)
        comparisons.append(dict(cq=index, rows=expected, cypher_chars=len(cypher), sparql_chars=len(sparql),
                                cypher_ms=sorted(cypher_ms)[2], sparql_ms=sorted(sparql_ms)[2]))
    assert reference[1] == [{"vm": "vm_01"}]
    assert reference[3] == [{"incident": "inc_01"}]
    assert reference[6] == [{"route": [f"vm_{i:02d}" for i in range(1, 6)], "hops": 4}]
    save("cypher.json", reference)
    save("sparql_vs_cypher.json", comparisons)
    print("10 CQ executed; 5 Cypher/SPARQL pairs agree", flush=True)
    return reference

def evaluate_t2c(admin, uri, reference, candidates):
    # A DB-managed reader account is the authorization boundary.
    password = secrets.token_urlsafe(24)
    username = "lab09_reader_" + secrets.token_hex(5)
    def system(query, **parameters):
        return admin.execute_query(query, parameters_=parameters, database_="system")
    system(f"CREATE USER {username} SET PASSWORD $password CHANGE NOT REQUIRED", password=password)
    try:
        system(f"GRANT ROLE reader TO {username}")
        roles, _, _ = system(f"SHOW USERS YIELD user, roles WHERE user='{username}' RETURN roles")
        role_names = sorted(roles[0]["roles"])
        assert "reader" in role_names and set(role_names) <= {"reader", "PUBLIC"}, role_names
        with GraphDatabase.driver(uri, auth=(username, password)) as reader:
            try:
                measure(reader, "CREATE (:Lab09WriteCheck)")
            except Neo4jError as error:
                if not error.code.startswith("Neo.ClientError.Security."):
                    raise
                denial = error.code
            else:
                raise AssertionError("Reader can write")
            results = []
            cases = [json.loads(line) for line in candidates.read_text(encoding="utf-8").splitlines() if line.strip()]
            assert sorted(case["id"] for case in cases) == list(range(1, 11))
            for case in cases:
                started = perf_counter()
                query = case["candidate"]
                result = dict(case)
                try:
                    match = re.search(r"\bLIMIT\s+(\d+)\s*$", query, flags=re.I)
                    if not match or not 1 <= int(match[1]) <= 100 or not re.match(r"\s*MATCH\b", query, re.I):
                        raise ValueError("Запит має починатися з MATCH і завершуватися LIMIT 1–100")
                    _, _, plan = measure(reader, "EXPLAIN " + query)
                    for status in plan.gql_status_objects:
                        if status.gql_status in {"01N50", "01N51", "01N52"} or (
                                status.classification == "UNRECOGNIZED"):
                            raise ValueError(status.status_description)
                    rows, _, summary = measure(reader, query)
                    result.update(rows=rows, correct=rows == reference[case["id"]],
                                  reason="Збіг з еталоном" if rows == reference[case["id"]] else "Відмінність від еталона")
                    assert summary.query_type == "r"
                except (Neo4jError, ValueError) as error:
                    result.update(correct=False, reason=str(error))
                result["elapsed_ms"] = (perf_counter() - started) * 1000
                results.append(result)
        correct = sum(item["correct"] for item in results)
        save("t2c.json", dict(roles=role_names, write_denied=denial, correct=correct,
                              total=len(results), accuracy=correct / len(results), cases=results))
        print(f"Text-to-Cypher: {correct}/{len(results)}", flush=True)
    finally:
        system(f"DROP USER {username} IF EXISTS")

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidates", type=Path, default=ROOT / "tests/t2c.jsonl")
    options = parser.parse_args()
    uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    password = os.getenv("NEO4J_PASSWORD") or getpass.getpass("Пароль Neo4j: ")
    with GraphDatabase.driver(uri, auth=("neo4j", password)) as admin:
        admin.verify_connectivity()
        def run(query):
            return measure(admin, query)[0]
        import_graph(run)
        reference = compare(admin)
        graph_analysis(run, admin)
        evaluate_t2c(admin, uri, reference, options.candidates)

if __name__ == "__main__":
    main()
