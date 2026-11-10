INSERT INTO users (username, email)
VALUES ('sample_user', 'sample@example.com')
ON DUPLICATE KEY UPDATE email = VALUES(email);

-- The sample user owns every part of COMCON002-1. This is the app's "I own this set"
-- query (POST /api/users/{id}/parts/from-set/{set_num}). Clearing the user's parts
-- first keeps the quantities the same when the script is re-run.
DELETE FROM user_parts
WHERE user_id = (SELECT id FROM users WHERE username = 'sample_user');

INSERT INTO user_parts (user_id, part_num, color_id, quantity)
SELECT u.id, ip.part_num, ip.color_id, ip.quantity
FROM users AS u
JOIN inventories AS i ON i.set_num = 'COMCON002-1'
JOIN inventory_parts AS ip ON ip.inventory_id = i.id
WHERE u.username = 'sample_user'
  AND ip.is_spare = 0
  AND i.version = (SELECT MAX(version) FROM inventories WHERE set_num = 'COMCON002-1')
ON DUPLICATE KEY UPDATE quantity = user_parts.quantity + VALUES(quantity);

-- Fixed dates keep the output stable across runs.
INSERT INTO user_completed_sets (user_id, set_num, completed_at)
SELECT id, 'COMCON002-1', '2026-10-15 10:00:00'
FROM users
WHERE username = 'sample_user'
ON DUPLICATE KEY UPDATE completed_at = VALUES(completed_at);

INSERT INTO user_completed_sets (user_id, set_num, completed_at)
SELECT id, '20004-1', '2026-10-20 10:00:00'
FROM users
WHERE username = 'sample_user'
ON DUPLICATE KEY UPDATE completed_at = VALUES(completed_at);

-- Feature 1 (R6): sets containing part 2339 in Dark Brown (colour 308), newest first.
-- The app's query (GET /api/parts/{part_num}/sets), first page of 48.
SELECT DISTINCT
    s.set_num,
    s.name,
    s.year,
    s.num_parts,
    t.name AS theme_name,
    parent.name AS parent_theme_name
FROM
    sets AS s
    JOIN inventories AS i ON i.set_num = s.set_num
    JOIN inventory_parts AS ip ON ip.inventory_id = i.id
    LEFT JOIN themes AS t ON t.id = s.theme_id
    LEFT JOIN themes AS parent ON parent.id = t.parent_id
WHERE
    ip.part_num = '2339'
    AND ip.color_id = 308
    AND ip.is_spare = 0
ORDER BY
    s.year DESC,
    s.set_num
LIMIT 48 OFFSET 0;

-- Feature 2 (R7): Indiana Jones sets (theme 264 and its direct subthemes) with at
-- least 10 pieces, fewest pieces first. The app's query (GET /api/sets), first page of 48.
SELECT
    s.set_num,
    s.name,
    s.year,
    s.num_parts,
    t.name AS theme_name,
    parent.name AS parent_theme_name
FROM
    sets AS s
    LEFT JOIN themes AS t ON s.theme_id = t.id
    LEFT JOIN themes AS parent ON t.parent_id = parent.id
WHERE
    (s.theme_id = 264 OR t.parent_id = 264)
    AND s.num_parts >= 10
ORDER BY
    s.num_parts IS NULL,
    s.num_parts ASC,
    s.name
LIMIT 48 OFFSET 0;

-- Feature 3 (R8): sets the sample user can build, biggest first.
-- The app's query (BUILDABLE_SQL in app.py, GET /api/users/{id}/buildable); the app
-- asks for one more row than the page size of 48 to know if there is another page.
WITH matched AS (
    SELECT
        ip.inventory_id,
        SUM(o.quantity >= ip.quantity) AS lots_covered,
        SUM(LEAST(ip.quantity, o.quantity)) AS pieces_owned
    FROM
        user_parts AS o
        JOIN inventory_parts AS ip
            ON ip.part_num = o.part_num
            AND ip.color_id = o.color_id
            AND ip.is_spare = 0
    WHERE
        o.user_id = (SELECT id FROM users WHERE username = 'sample_user')
    GROUP BY
        ip.inventory_id
),
coverage AS (
    SELECT
        m.inventory_id,
        it.pieces AS pieces_required,
        m.pieces_owned,
        it.lots - m.lots_covered AS lots_missing
    FROM
        matched AS m
        JOIN inventory_totals AS it ON it.inventory_id = m.inventory_id
)
SELECT
    s.set_num,
    s.name,
    s.year,
    CAST(cov.pieces_required AS SIGNED) AS pieces_required,
    CAST(cov.pieces_owned AS SIGNED) AS pieces_owned,
    CAST(cov.lots_missing AS SIGNED) AS lots_missing
FROM
    coverage AS cov
    JOIN inventories AS i ON i.id = cov.inventory_id
    JOIN sets AS s ON s.set_num = i.set_num
WHERE
    i.version = (SELECT MAX(i2.version) FROM inventories AS i2 WHERE i2.set_num = i.set_num)
    AND cov.lots_missing = 0
ORDER BY
    cov.pieces_required DESC,
    s.set_num
LIMIT 49;

-- Fetch the sample user's completed sets.
SELECT
    s.set_num,
    s.name,
    ucs.completed_at
FROM
    user_completed_sets AS ucs
    JOIN sets AS s ON s.set_num = ucs.set_num
WHERE
    ucs.user_id = (
        SELECT id
        FROM users
        WHERE username = 'sample_user'
    )
ORDER BY
    ucs.completed_at DESC;

-- Find parts related to part 2339, with the relationship type and which side 2339 is on.
SELECT
    r.rel_type,
    'child' AS role,
    p.part_num,
    p.name
FROM
    part_relationships AS r
    JOIN parts AS p ON p.part_num = r.parent_part_num
WHERE
    r.child_part_num = '2339'
UNION ALL
SELECT
    r.rel_type,
    'parent' AS role,
    p.part_num,
    p.name
FROM
    part_relationships AS r
    JOIN parts AS p ON p.part_num = r.child_part_num
WHERE
    r.parent_part_num = '2339'
ORDER BY
    rel_type,
    role,
    part_num;

-- "Remove" button: the app runs
--   DELETE FROM user_completed_sets WHERE user_id = %s AND set_num = %s
-- with the demo user's id and the set number as parameters.
DELETE FROM user_completed_sets
WHERE
    user_id = (
        SELECT id
        FROM users
        WHERE username = 'sample_user'
    )
    AND set_num = '20004-1';

-- Fetch the completed sets again: only COMCON002-1 is left.
SELECT
    s.set_num,
    s.name,
    ucs.completed_at
FROM
    user_completed_sets AS ucs
    JOIN sets AS s ON s.set_num = ucs.set_num
WHERE
    ucs.user_id = (
        SELECT id
        FROM users
        WHERE username = 'sample_user'
    )
ORDER BY
    ucs.completed_at DESC;
