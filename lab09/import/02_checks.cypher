MATCH (n:Resource) RETURN count(n) AS nodes;
MATCH (:Resource)-[r]->(:Resource) RETURN count(r) AS relationships;
SHOW CONSTRAINTS YIELD name, type ORDER BY name;
SHOW INDEXES YIELD name, type, state ORDER BY name;
// Окрема транзакція. Очікувана помилка Neo.ClientError.Schema.ConstraintValidationFailed.
CREATE (:Resource {id:'srv_01'});
