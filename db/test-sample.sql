SELECT s.set_num, s.name, s.year, s.num_parts, t.name AS theme_name
FROM sets s
INNER JOIN themes t ON s.theme_id = t.id
WHERE s.set_num IN ('75192-1', '75355-1', '10316-1')
ORDER BY s.set_num;
