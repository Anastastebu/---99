# Імпорт і цілісність

Таблиця 9. Перевірка ідемпотентності імпорту

| Запуск | Вузлів | Зв’язків |
|---|---:|---:|
| Перший | 120 | 216 |
| Повторний | 120 | 216 |

Джерело вузлів — nodes.csv. Джерело зв’язків — relationships.csv. Тип зв’язку вибирається окремим оператором із визначеного набору. MERGE знаходить вузол за id і зв’язок за впорядкованою парою кінців та типом. SET оновлює властивості без створення дубліката.

Унікальні обмеження: incident_id, resource_id. Окремі індекси: incident_severity (ONLINE), resource_site (ONLINE).

Контрольна вставка `CREATE (:Resource {id:'srv_01'})` відхилена.

```text
Neo.ClientError.Schema.ConstraintValidationFailed
Node(0) already exists with label `Resource` and property `id` = 'srv_01'
```
