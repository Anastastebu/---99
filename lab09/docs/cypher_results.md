# Результати запитів Cypher

## CQ01

Які ВМ працюють на srv_01 через гіпервізор?

```cypher
MATCH (:ComputeServer {id:'srv_01'})-[:HOSTS_RESOURCE]->(:Hypervisor)-[:RUNS_VIRTUAL_MACHINE]->(v:VirtualMachine)
RETURN v.id AS vm ORDER BY vm;
```

**Результат** `[{"vm": "vm_01"}]`

Через гіпервізор hyp_01 сервер запускає vm_01.

## CQ02

Які сенсори моніторять srv_01?

```cypher
MATCH (s:Sensor)-[:MONITORS_RESOURCE]->(:ComputeServer {id:'srv_01'})
RETURN s.id AS sensor ORDER BY sensor;
```

**Результат** `[{"sensor": "sensor_01"}, {"sensor": "sensor_05"}]`

Сервер srv_01 моніторять свій sensor_01 та сусідній sensor_05 того самого майданчика.

## CQ03

Які інциденти high зачепили vm_02?

```cypher
MATCH (i:Incident {severity:'high'})-[:AFFECTS]->(:VirtualMachine {id:'vm_02'})
RETURN i.id AS incident ORDER BY incident;
```

**Результат** `[{"incident": "inc_01"}]`

Інцидент inc_01 має high і зачіпає vm_02. Інцидент inc_02 теж зачіпає vm_02, але має low.

## CQ04

Скільки різних інцидентів виявлено сенсорами кожного майданчика?

```cypher
MATCH (i:Incident)-[:DETECTED_BY]->(s:Sensor)
WITH s.site AS site, count(DISTINCT i) AS incidents
RETURN site, incidents ORDER BY site;
```

**Результат** `[{"site": "site_1", "incidents": 5}, {"site": "site_2", "incidents": 5}, {"site": "site_3", "incidents": 5}, {"site": "site_4", "incidents": 5}]`

На кожному майданчику є п’ять різних інцидентів із сенсорами цього майданчика.

## CQ05

Яка безпосередня залежність vm_01?

```cypher
MATCH (v:VirtualMachine {id:'vm_01'})
OPTIONAL MATCH (v)-[:DEPENDS_ON]->(d:VirtualMachine)
RETURN v.id AS vm, d.id AS dependency ORDER BY dependency;
```

**Результат** `[{"vm": "vm_01", "dependency": "vm_02"}]`

Безпосередня залежність vm_01 — vm_02.

## CQ06

Який найкоротший маршрут залежностей vm_01 → vm_05?

```cypher
MATCH (a:VirtualMachine {id:'vm_01'}), (b:VirtualMachine {id:'vm_05'})
MATCH p = shortestPath((a)-[:DEPENDS_ON*..6]->(b))
RETURN [n IN nodes(p) | n.id] AS route, length(p) AS hops;
```

**Результат** `[{"route": ["vm_01", "vm_02", "vm_03", "vm_04", "vm_05"], "hops": 4}]`

Найкоротший маршрут складається з чотирьох ребер.

## CQ07

Які Firewall захищають vm_01 зі confidence ≥ 0.9 станом на 2026-11-18?

```cypher
MATCH (f:Firewall)-[r:PROTECTS]->(:VirtualMachine {id:'vm_01'})
WHERE r.confidence >= 0.9 AND r.validFrom <= date('2026-11-18')
RETURN f.id AS firewall, r.source AS source ORDER BY firewall;
```

**Результат** `[{"firewall": "fw_01", "source": "LR09-demo-rule-v1"}, {"firewall": "fw_05", "source": "LR09-demo-rule-v1"}]`

fw_01 і fw_05 мають зв’язки, що проходять фільтри дати та довіри.

## CQ08

Яка безпосередня залежність vm_05, якщо вона є?

```cypher
MATCH (v:VirtualMachine {id:'vm_05'})
OPTIONAL MATCH (v)-[:DEPENDS_ON]->(d:VirtualMachine)
RETURN v.id AS vm, d.id AS dependency ORDER BY dependency;
```

**Результат** `[{"vm": "vm_05", "dependency": null}]`

У vm_05 немає вихідного DEPENDS_ON. OPTIONAL MATCH зберігає рядок із null.

## CQ09

Від яких ВМ залежить vm_01 на глибині 1–4?

```cypher
MATCH p = (:VirtualMachine {id:'vm_01'})-[:DEPENDS_ON*1..4]->(d:VirtualMachine)
RETURN d.id AS dependency, min(length(p)) AS depth ORDER BY depth, dependency;
```

**Результат** `[{"dependency": "vm_02", "depth": 1}, {"dependency": "vm_03", "depth": 2}, {"dependency": "vm_04", "depth": 3}, {"dependency": "vm_05", "depth": 4}]`

vm_01 прямо або опосередковано залежить від vm_02, vm_03, vm_04 та vm_05.

## CQ10

Які ВМ постраждають при відмові vm_05 на глибині 1–4?

```cypher
MATCH p = (:VirtualMachine {id:'vm_05'})<-[:DEPENDS_ON*1..4]-(v:VirtualMachine)
RETURN v.id AS affected, min(length(p)) AS depth ORDER BY depth, affected;
```

**Результат** `[{"affected": "vm_04", "depth": 1}, {"affected": "vm_03", "depth": 2}, {"affected": "vm_02", "depth": 3}, {"affected": "vm_01", "depth": 4}]`

Відмова vm_05 зачіпає vm_04, vm_03, vm_02, vm_01 на глибині від 1 до 4.

## Ручна перевірка малого підграфа

| CQ | Вузли й ребра малого підграфа | Перевірений результат |
|---|---|---|
| 01 | srv_01 → hyp_01 → vm_01. На обох кроках по одному вихідному зв’язку потрібного типу. | vm_01 |
| 03 | inc_01 і inc_02 мають AFFECTS до vm_02. Значення severity — high і low відповідно. | inc_01 |
| 06 | vm_01 → vm_02 → vm_03 → vm_04 → vm_05. Вихідний DEPENDS_ON кожної ВМ у ланцюзі веде лише до наступної. | Єдиний маршрут має 4 ребра. |

CQ09 показує, від чого залежить vm_01. CQ10 обходить зв’язки у зворотному напрямку і показує, кого зачепить відмова vm_05. В обох запитах максимальна глибина дорівнює 4.
