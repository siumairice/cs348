-- test-production.sql: the feature queries run on the production dataset.
--
-- Load the full Rebrickable data first (the default for `docker compose up`), then:
--   docker compose exec -T db mysql -uroot -pcs348pass --default-character-set=utf8mb4 \
--     --table lego_sets < db/test-production.sql > db/test-production.out
--
-- Each query is the one the app runs (app.py), with its %s parameters filled in.
-- Long results are cut to the top 10 rows, and a count shows the full size.
-- User data goes to a separate `production_user`, so the website's demo user is untouched.

-- ---------------------------------------------------------------------------
-- Setup: a test user who owns every part of Rivendell (10316-1, 6,088 non-spare pieces)
-- and has completed two sets on fixed dates, so the output is the same every run.
-- ---------------------------------------------------------------------------
INSERT INTO users (username, email)
VALUES ('production_user', 'production@example.com')
ON DUPLICATE KEY UPDATE email = VALUES(email);

SET @user_id = (SELECT id FROM users WHERE username = 'production_user');

DELETE FROM user_parts WHERE user_id = @user_id;
DELETE FROM user_completed_sets WHERE user_id = @user_id;

-- "I own this set" button (POST /api/users/{id}/parts/from-set/10316-1).
INSERT INTO user_parts (user_id, part_num, color_id, quantity)
SELECT @user_id, ip.part_num, ip.color_id, ip.quantity
FROM inventories i
JOIN inventory_parts ip ON ip.inventory_id = i.id
WHERE i.set_num = '10316-1'
  AND ip.is_spare = 0
  AND i.version = (SELECT MAX(version) FROM inventories WHERE set_num = '10316-1')
ON DUPLICATE KEY UPDATE quantity = user_parts.quantity + VALUES(quantity);

-- "Mark as Completed" button (POST /api/completed/{set_num}), with fixed dates.
INSERT INTO user_completed_sets (user_id, set_num, completed_at)
VALUES
    (@user_id, '10316-1', '2026-10-15 10:00:00'),
    (@user_id, '75192-1', '2026-10-20 10:00:00');

SELECT
    (SELECT COUNT(*) FROM user_parts WHERE user_id = @user_id) AS owned_lots,
    (SELECT SUM(quantity) FROM user_parts WHERE user_id = @user_id) AS owned_pieces,
    (SELECT COUNT(*) FROM user_completed_sets WHERE user_id = @user_id) AS completed_sets;

-- ---------------------------------------------------------------------------
-- Feature 1 (R6): sets that contain a given part in a given colour
-- (GET /api/parts/{part_num}/colors and GET /api/parts/{part_num}/sets).
-- Input: part 3001 (Brick 2 x 4) in colour 4 (Red).
-- ---------------------------------------------------------------------------
SELECT 'Feature 1: sets containing part 3001 in Red (colour 4)' AS feature;

-- The colour drop-down: colours the part comes in, with set counts (top 10 of 80).
-- plan: Feature 1, colours a part comes in
SELECT
    c.id,
    c.name,
    c.rgb,
    COUNT(DISTINCT s.set_num) AS set_count
FROM inventory_parts ip
JOIN inventories i ON i.id = ip.inventory_id
JOIN sets s ON s.set_num = i.set_num
JOIN colors c ON c.id = ip.color_id
WHERE ip.part_num = '3001'
  AND ip.is_spare = 0
GROUP BY c.id, c.name, c.rgb
ORDER BY set_count DESC, c.name
LIMIT 10;

-- plan: Feature 1, count sets containing a part in a colour
SELECT COUNT(DISTINCT s.set_num) AS total
FROM sets AS s
JOIN inventories AS i ON i.set_num = s.set_num
JOIN inventory_parts AS ip ON ip.inventory_id = i.id
LEFT JOIN themes AS t ON t.id = s.theme_id
LEFT JOIN themes AS parent ON parent.id = t.parent_id
WHERE ip.part_num = '3001'
  AND ip.color_id = 4
  AND ip.is_spare = 0;

-- plan: Feature 1, first page of sets containing a part in a colour
SELECT DISTINCT
    s.set_num,
    s.name,
    s.year,
    s.num_parts,
    t.name AS theme_name,
    parent.name AS parent_theme_name
FROM sets AS s
JOIN inventories AS i ON i.set_num = s.set_num
JOIN inventory_parts AS ip ON ip.inventory_id = i.id
LEFT JOIN themes AS t ON t.id = s.theme_id
LEFT JOIN themes AS parent ON parent.id = t.parent_id
WHERE ip.part_num = '3001'
  AND ip.color_id = 4
  AND ip.is_spare = 0
ORDER BY s.year DESC, s.set_num
LIMIT 10 OFFSET 0;

-- ---------------------------------------------------------------------------
-- Feature 2 (R7): search sets by theme and minimum piece count (GET /api/sets).
-- Input: theme 126 (the top-level "Space" theme; two other themes are also
-- named "Space", which is why the app filters by id), at least 500 pieces,
-- fewest pieces first. The app includes the theme's direct subthemes.
-- ---------------------------------------------------------------------------
SELECT 'Feature 2: Space (theme 126) sets with at least 500 pieces' AS feature;

SELECT id, name, parent_id FROM themes WHERE name = 'Space' ORDER BY id;

-- plan: Feature 2, count matching sets
SELECT COUNT(*) AS total
FROM sets s
LEFT JOIN themes t ON s.theme_id = t.id
LEFT JOIN themes parent ON t.parent_id = parent.id
WHERE (s.theme_id = 126 OR t.parent_id = 126)
  AND s.num_parts >= 500;

-- plan: Feature 2, first page of matching sets
SELECT
    s.set_num,
    s.name,
    s.year,
    s.num_parts,
    t.name AS theme_name,
    parent.name AS parent_theme_name
FROM sets s
LEFT JOIN themes t ON s.theme_id = t.id
LEFT JOIN themes parent ON t.parent_id = parent.id
WHERE (s.theme_id = 126 OR t.parent_id = 126)
  AND s.num_parts >= 500
ORDER BY s.num_parts IS NULL, s.num_parts ASC, s.name
LIMIT 10 OFFSET 0;

-- ---------------------------------------------------------------------------
-- Feature 3 (R8): sets the user can build with their parts
-- (GET /api/users/{id}/buildable, BUILDABLE_SQL in app.py).
-- Input: production_user, who owns all of Rivendell's parts.
-- ---------------------------------------------------------------------------
SELECT 'Feature 3: sets production_user can build (owns all Rivendell parts)' AS feature;

-- Buildable sets, biggest first.
-- plan: Feature 3, buildable sets (app query)
WITH matched AS (
    SELECT
        ip.inventory_id,
        SUM(o.quantity >= ip.quantity) AS lots_covered,
        SUM(LEAST(ip.quantity, o.quantity)) AS pieces_owned
    FROM user_parts o
    JOIN inventory_parts ip
      ON ip.part_num = o.part_num
     AND ip.color_id = o.color_id
     AND ip.is_spare = 0
    WHERE o.user_id = @user_id
    GROUP BY ip.inventory_id
),
coverage AS (
    SELECT
        m.inventory_id,
        it.pieces AS pieces_required,
        m.pieces_owned,
        it.lots - m.lots_covered AS lots_missing
    FROM matched m
    JOIN inventory_totals it ON it.inventory_id = m.inventory_id
)
SELECT
    s.set_num,
    s.name,
    s.year,
    CAST(cov.pieces_required AS SIGNED) AS pieces_required,
    CAST(cov.pieces_owned AS SIGNED) AS pieces_owned,
    CAST(cov.lots_missing AS SIGNED) AS lots_missing
FROM coverage cov
JOIN inventories i ON i.id = cov.inventory_id
JOIN sets s ON s.set_num = i.set_num
WHERE i.version = (SELECT MAX(i2.version) FROM inventories i2 WHERE i2.set_num = i.set_num)
  AND cov.lots_missing = 0
ORDER BY cov.pieces_required DESC, s.set_num
LIMIT 10;

-- "Almost there": sets the user can't build yet, closest first.
-- plan: Feature 3, almost-buildable sets (app query)
WITH matched AS (
    SELECT
        ip.inventory_id,
        SUM(o.quantity >= ip.quantity) AS lots_covered,
        SUM(LEAST(ip.quantity, o.quantity)) AS pieces_owned
    FROM user_parts o
    JOIN inventory_parts ip
      ON ip.part_num = o.part_num
     AND ip.color_id = o.color_id
     AND ip.is_spare = 0
    WHERE o.user_id = @user_id
    GROUP BY ip.inventory_id
),
coverage AS (
    SELECT
        m.inventory_id,
        it.pieces AS pieces_required,
        m.pieces_owned,
        it.lots - m.lots_covered AS lots_missing
    FROM matched m
    JOIN inventory_totals it ON it.inventory_id = m.inventory_id
)
SELECT
    s.set_num,
    s.name,
    s.year,
    CAST(cov.pieces_required AS SIGNED) AS pieces_required,
    CAST(cov.pieces_owned AS SIGNED) AS pieces_owned,
    CAST(cov.lots_missing AS SIGNED) AS lots_missing
FROM coverage cov
JOIN inventories i ON i.id = cov.inventory_id
JOIN sets s ON s.set_num = i.set_num
WHERE i.version = (SELECT MAX(i2.version) FROM inventories i2 WHERE i2.set_num = i.set_num)
  AND cov.lots_missing > 0
ORDER BY cov.pieces_owned / cov.pieces_required DESC, cov.lots_missing, s.set_num
LIMIT 10;

-- Cross-check with the report's NOT EXISTS template (R8), which checks every set:
-- both forms must find the same number of buildable sets.
-- plan: Feature 3, report's NOT EXISTS template (for comparison)
SELECT COUNT(*) AS buildable_sets_report_template
FROM sets s
JOIN inventories i ON i.set_num = s.set_num
WHERE i.version = (SELECT MAX(i2.version) FROM inventories i2 WHERE i2.set_num = s.set_num)
  AND EXISTS (
      SELECT 1 FROM inventory_parts r WHERE r.inventory_id = i.id AND r.is_spare = 0
  )
  AND NOT EXISTS (
      SELECT 1
      FROM inventory_parts AS required
      WHERE required.inventory_id = i.id
        AND required.is_spare = 0
        AND required.quantity > COALESCE(
            (
                SELECT SUM(owned.quantity)
                FROM user_parts AS owned
                WHERE owned.user_id = @user_id
                  AND owned.part_num = required.part_num
                  AND owned.color_id = required.color_id
            ),
            0
        )
  );

-- ---------------------------------------------------------------------------
-- Feature 4 (R9): the user's completed sets, newest first (GET /api/completed).
-- ---------------------------------------------------------------------------
SELECT 'Feature 4: production_user completed sets' AS feature;

-- plan: Feature 4, completed sets
SELECT
    s.set_num,
    s.name,
    ucs.completed_at
FROM
    user_completed_sets AS ucs
    JOIN sets AS s ON s.set_num = ucs.set_num
WHERE
    ucs.user_id = @user_id
ORDER BY
    ucs.completed_at DESC;

-- "Remove" button (DELETE /api/completed/75192-1), then list again.
DELETE FROM user_completed_sets WHERE user_id = @user_id AND set_num = '75192-1';

SELECT
    s.set_num,
    s.name,
    ucs.completed_at
FROM
    user_completed_sets AS ucs
    JOIN sets AS s ON s.set_num = ucs.set_num
WHERE
    ucs.user_id = @user_id
ORDER BY
    ucs.completed_at DESC;

-- ---------------------------------------------------------------------------
-- Feature 5 (R10): parts related to a given part (GET /api/parts/{part_num}).
-- Input: part 3001 (Brick 2 x 4), which has 100 relationships.
-- ---------------------------------------------------------------------------
SELECT 'Feature 5: parts related to 3001 (Brick 2 x 4)' AS feature;

SELECT rel_type, role, COUNT(*) AS count
FROM (
    SELECT rel_type, 'child' AS role FROM part_relationships WHERE child_part_num = '3001'
    UNION ALL
    SELECT rel_type, 'parent' AS role FROM part_relationships WHERE parent_part_num = '3001'
) AS ends
GROUP BY rel_type, role
ORDER BY rel_type, role;

-- plan: Feature 5, related parts
SELECT r.rel_type, 'child' AS role, p.part_num, p.name, c.name AS category_name
FROM part_relationships r
JOIN parts p ON p.part_num = r.parent_part_num
JOIN part_categories c ON c.id = p.part_cat_id
WHERE r.child_part_num = '3001'
UNION ALL
SELECT r.rel_type, 'parent' AS role, p.part_num, p.name, c.name AS category_name
FROM part_relationships r
JOIN parts p ON p.part_num = r.child_part_num
JOIN part_categories c ON c.id = p.part_cat_id
WHERE r.parent_part_num = '3001'
ORDER BY FIELD(rel_type, 'P', 'T', 'M', 'A', 'B', 'R'), role DESC, part_num
LIMIT 10 OFFSET 0;

-- ---------------------------------------------------------------------------
-- Cleanup: remove the test user's data so the script can be re-run.
-- ---------------------------------------------------------------------------
DELETE FROM user_parts WHERE user_id = @user_id;
DELETE FROM user_completed_sets WHERE user_id = @user_id;
DELETE FROM users WHERE id = @user_id;
