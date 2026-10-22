-- find all sets containing a specific piece in a specific colour, sorted by year and set number
SELECT DISTINCT
    s.set_num,
    s.name,
    s.year
FROM
    sets AS s
    JOIN inventories AS i ON i.set_num = s.set_num
    JOIN inventory_parts AS ip ON ip.inventory_id = i.id
WHERE
    ip.part_num = '3001'
    AND ip.color_id = 4
    AND ip.is_spare = 0
ORDER BY
    s.year DESC,
    s.set_num;

-- find sets with a specific theme (in this case Space)
-- we add a constraint for at least 10 pieces since we don't think the customer
-- would want to be searching for very small sets.
SELECT
    s.set_num,
    s.name,
    s.year,
    s.num_parts
FROM
    sets AS s
    JOIN themes AS t ON t.id = s.theme_id
WHERE
    t.name = 'Space'
    AND s.num_parts >= 10
ORDER BY
    s.num_parts ASC,
    s.set_num;

-- check if a user can build a specific set (in this case 75192-1) based on the parts they own
-- first we find the set and its inventory
-- then for every part in the inventory we check if the user owns enough of it
-- if they don't then they can't build the set
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
                        owned.user_id = 1
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
    s.set_num = '75192-1'
    AND i.version = (
        SELECT
            MAX(i2.version)
        FROM
            inventories AS i2
        WHERE
            i2.set_num = s.set_num
    );

-- fetch user's completed sets (in this case user 1)
SELECT
    s.set_num,
    s.name,
    ucs.completed_at
FROM
    user_completed_sets AS ucs
    JOIN sets AS s ON s.set_num = ucs.set_num
WHERE
    ucs.user_id = 1
ORDER BY
    ucs.completed_at DESC;