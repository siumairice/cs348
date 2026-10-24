INSERT INTO users (username, email)
VALUES ('sample_user', 'sample@example.com')
ON DUPLICATE KEY UPDATE email = VALUES(email);

INSERT INTO user_parts (user_id, part_num, color_id, quantity)
SELECT id, '2339', 308, 1
FROM users
WHERE username = 'sample_user'
ON DUPLICATE KEY UPDATE quantity = VALUES(quantity);

INSERT INTO user_completed_sets (user_id, set_num, completed_at)
SELECT id, 'COMCON002-1', CURRENT_TIMESTAMP
FROM users
WHERE username = 'sample_user'
ON DUPLICATE KEY UPDATE completed_at = VALUES(completed_at);

-- Find sets containing part 2339 in Dark Brown (color 308).
SELECT DISTINCT
    s.set_num,
    s.name,
    s.year
FROM
    sets AS s
    JOIN inventories AS i ON i.set_num = s.set_num
    JOIN inventory_parts AS ip ON ip.inventory_id = i.id
WHERE
    ip.part_num = '2339'
    AND ip.color_id = 308
    AND ip.is_spare = 0
ORDER BY
    s.year DESC,
    s.set_num;

-- Find sets in the sample's Indiana Jones theme.
SELECT
    s.set_num,
    s.name,
    s.year,
    s.num_parts
FROM
    sets AS s
    JOIN themes AS t ON t.id = s.theme_id
WHERE
    t.name = 'Indiana Jones'
    AND s.num_parts >= 10
ORDER BY
    t.name,
    s.num_parts ASC,
    s.set_num;

-- Check whether the sample user owns enough parts to build each set.
SELECT
    s.set_num,
    s.name,
    NOT EXISTS (
        SELECT
            1
        FROM
            inventory_parts AS required
        WHERE
            required.inventory_id = i.id
            AND required.is_spare = 0
            AND required.quantity > COALESCE(
                (
                    SELECT
                        SUM(owned.quantity)
                    FROM
                        user_parts AS owned
                    WHERE
                        owned.user_id = (
                            SELECT id
                            FROM users
                            WHERE username = 'sample_user'
                        )
                        AND owned.part_num = required.part_num
                        AND owned.color_id = required.color_id
                ),
                0
            )
    ) AS can_build
FROM
    sets AS s
    JOIN inventories AS i ON i.set_num = s.set_num
WHERE
    i.version = (
        SELECT
            MAX(i2.version)
        FROM
            inventories AS i2
        WHERE
            i2.set_num = s.set_num
    )
ORDER BY
    s.set_num;

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
