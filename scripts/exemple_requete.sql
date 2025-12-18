-- Exemple: Voir tous les articles avec sentiment
-- Copiez cette requête dans SQLite CLI ou un outil graphique

SELECT 
    r.raw_data_id as id,
    s.name as source,
    r.title,
    mo.label as sentiment,
    mo.score as sentiment_score
FROM raw_data r
JOIN source s ON r.source_id = s.source_id
LEFT JOIN model_output mo ON r.raw_data_id = mo.raw_data_id 
    AND mo.model_name = 'sentiment_keyword'
ORDER BY r.collected_at DESC
LIMIT 20;
