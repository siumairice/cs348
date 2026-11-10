from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Query, Request, Response
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from mysql.connector import Error, IntegrityError, errorcode
from pydantic import BaseModel, Field

from database import connect_with_retry, get_connection

# There is no login yet, so every request acts as this demo user.
# It is the same user that db/test-sample.sql seeds.
DEMO_USERNAME = "sample_user"
DEMO_EMAIL = "sample@example.com"
DEMO_USER_ID = None


def ensure_demo_user(connection):
    cursor = connection.cursor()
    try:
        cursor.execute(
            """
            INSERT INTO users (username, email)
            VALUES (%s, %s)
            ON DUPLICATE KEY UPDATE email = VALUES(email)
            """,
            (DEMO_USERNAME, DEMO_EMAIL),
        )
        connection.commit()
        cursor.execute("SELECT id FROM users WHERE username = %s", (DEMO_USERNAME,))
        return cursor.fetchone()[0]
    finally:
        cursor.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    global DEMO_USER_ID
    connection = connect_with_retry()
    try:
        DEMO_USER_ID = ensure_demo_user(connection)
    finally:
        connection.close()
    yield


app = FastAPI(
    title="LEGO Sets Explorer",
    lifespan=lifespan,
)
templates = Jinja2Templates(directory="src")

SORT_ORDERS = {
    "year_desc": "s.year DESC, s.name",
    "year_asc": "s.year ASC, s.name",
    "parts_desc": "s.num_parts IS NULL, s.num_parts DESC, s.name",
    "parts_asc": "s.num_parts IS NULL, s.num_parts ASC, s.name",
    "name": "s.name, s.year DESC",
}


def run_write(sql, params=()):
    """Run one INSERT/UPDATE/DELETE, commit it, and return the affected row count."""
    connection = None
    cursor = None
    try:
        connection = get_connection()
        cursor = connection.cursor()
        cursor.execute(sql, params)
        connection.commit()
        return cursor.rowcount
    except IntegrityError as exc:
        if exc.errno == errorcode.ER_DUP_ENTRY:
            raise HTTPException(status_code=409, detail="Already exists") from exc
        if exc.errno == errorcode.ER_NO_REFERENCED_ROW_2:
            raise HTTPException(status_code=404, detail="Referenced row not found") from exc
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Error as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    finally:
        if cursor is not None:
            cursor.close()
        if connection is not None and connection.is_connected():
            connection.close()


def run_query(sql, params=(), one=False):
    connection = None
    cursor = None
    try:
        connection = get_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute(sql, params)
        return cursor.fetchone() if one else cursor.fetchall()
    except Error as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    finally:
        if cursor is not None:
            cursor.close()
        if connection is not None and connection.is_connected():
            connection.close()


def home(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={},
    )


@app.get("/api/sets")
def list_sets(
    q: str = Query(default=""),
    theme_id: int | None = None,
    year_min: int | None = None,
    year_max: int | None = None,
    parts_min: int | None = None,
    parts_max: int | None = None,
    sort: str = Query(default="year_desc"),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
):
    if sort not in SORT_ORDERS:
        raise HTTPException(status_code=400, detail=f"Unknown sort: {sort}")

    conditions = []
    params = []
    if q:
        pattern = f"%{q}%"
        conditions.append(
            "(s.name LIKE %s OR s.set_num LIKE %s OR t.name LIKE %s OR parent.name LIKE %s)"
        )
        params += [pattern, pattern, pattern, pattern]
    if theme_id is not None:
        # Include sets from direct subthemes so picking "Star Wars" also finds its children.
        conditions.append("(s.theme_id = %s OR t.parent_id = %s)")
        params += [theme_id, theme_id]
    if year_min is not None:
        conditions.append("s.year >= %s")
        params.append(year_min)
    if year_max is not None:
        conditions.append("s.year <= %s")
        params.append(year_max)
    if parts_min is not None:
        conditions.append("s.num_parts >= %s")
        params.append(parts_min)
    if parts_max is not None:
        conditions.append("s.num_parts <= %s")
        params.append(parts_max)

    where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    joins = """
        FROM sets s
        LEFT JOIN themes t ON s.theme_id = t.id
        LEFT JOIN themes parent ON t.parent_id = parent.id
    """

    total = run_query(f"SELECT COUNT(*) AS total {joins} {where}", params, one=True)
    sets = run_query(
        f"""
        SELECT
            s.set_num,
            s.name,
            s.year,
            s.num_parts,
            s.img_url,
            s.theme_id,
            t.name AS theme_name,
            parent.name AS parent_theme_name
        {joins}
        {where}
        ORDER BY {SORT_ORDERS[sort]}
        LIMIT %s OFFSET %s
        """,
        params + [limit, offset],
    )
    return {"total": total["total"], "limit": limit, "offset": offset, "sets": sets}


@app.get("/api/sets/{set_num}")
def get_set(set_num: str):
    row = run_query(
        """
        SELECT
            s.set_num,
            s.name,
            s.year,
            s.num_parts,
            s.img_url,
            s.theme_id,
            t.name AS theme_name,
            t.parent_id AS parent_theme_id,
            parent.name AS parent_theme_name
        FROM sets s
        LEFT JOIN themes t ON s.theme_id = t.id
        LEFT JOIN themes parent ON t.parent_id = parent.id
        WHERE s.set_num = %s
        """,
        (set_num,),
        one=True,
    )
    if row is None:
        raise HTTPException(status_code=404, detail="Set not found")

    related = run_query(
        """
        SELECT set_num, name, year, num_parts, img_url
        FROM sets
        WHERE theme_id = %s AND set_num <> %s
        ORDER BY ABS(year - %s), name
        LIMIT 8
        """,
        (row["theme_id"], set_num, row["year"]),
    )
    completed = run_query(
        """
        SELECT completed_at
        FROM user_completed_sets
        WHERE user_id = %s AND set_num = %s
        """,
        (DEMO_USER_ID, set_num),
        one=True,
    )
    row["completed_at"] = completed["completed_at"] if completed else None
    return {"set": row, "related": related}


@app.get("/api/completed")
def list_completed():
    sets = run_query(
        """
        SELECT
            s.set_num,
            s.name,
            ucs.completed_at
        FROM
            user_completed_sets AS ucs
            JOIN sets AS s ON s.set_num = ucs.set_num
        WHERE
            ucs.user_id = %s
        ORDER BY
            ucs.completed_at DESC
        """,
        (DEMO_USER_ID,),
    )
    return {"sets": sets}


@app.post("/api/completed/{set_num}", status_code=201)
def mark_completed(set_num: str):
    # completed_at defaults to CURRENT_TIMESTAMP. The (user_id, set_num) primary key
    # rejects a second insert, which run_write turns into a 409. The original date stays.
    try:
        run_write(
            "INSERT INTO user_completed_sets (user_id, set_num) VALUES (%s, %s)",
            (DEMO_USER_ID, set_num),
        )
    except HTTPException as exc:
        if exc.status_code == 409:
            raise HTTPException(status_code=409, detail="Set already completed") from exc
        if exc.status_code == 404:
            raise HTTPException(status_code=404, detail="Set not found") from exc
        raise
    return run_query(
        """
        SELECT set_num, completed_at
        FROM user_completed_sets
        WHERE user_id = %s AND set_num = %s
        """,
        (DEMO_USER_ID, set_num),
        one=True,
    )


@app.delete("/api/completed/{set_num}")
def remove_completed(set_num: str):
    removed = run_write(
        "DELETE FROM user_completed_sets WHERE user_id = %s AND set_num = %s",
        (DEMO_USER_ID, set_num),
    )
    return {"removed": removed > 0}


@app.get("/api/themes")
def list_themes(q: str = Query(default="")):
    themes = run_query(
        """
        SELECT
            t.id,
            t.name,
            t.parent_id,
            parent.name AS parent_name,
            COUNT(s.set_num) AS set_count,
            MIN(s.year) AS first_year,
            MAX(s.year) AS last_year
        FROM themes t
        LEFT JOIN themes parent ON t.parent_id = parent.id
        LEFT JOIN sets s ON s.theme_id = t.id
        WHERE %s = '' OR t.name LIKE %s OR parent.name LIKE %s
        GROUP BY t.id, t.name, t.parent_id, parent.name
        ORDER BY t.name
        """,
        (q, f"%{q}%", f"%{q}%"),
    )
    return {"themes": themes}


@app.get("/api/themes/{theme_id}")
def get_theme(theme_id: int):
    theme = run_query(
        """
        SELECT t.id, t.name, t.parent_id, parent.name AS parent_name
        FROM themes t
        LEFT JOIN themes parent ON t.parent_id = parent.id
        WHERE t.id = %s
        """,
        (theme_id,),
        one=True,
    )
    if theme is None:
        raise HTTPException(status_code=404, detail="Theme not found")

    subthemes = run_query(
        """
        SELECT t.id, t.name, COUNT(s.set_num) AS set_count
        FROM themes t
        LEFT JOIN sets s ON s.theme_id = t.id
        WHERE t.parent_id = %s
        GROUP BY t.id, t.name
        ORDER BY set_count DESC, t.name
        """,
        (theme_id,),
    )
    stats = run_query(
        """
        SELECT
            COUNT(*) AS set_count,
            MIN(s.year) AS first_year,
            MAX(s.year) AS last_year,
            ROUND(AVG(s.num_parts)) AS avg_parts,
            MAX(s.num_parts) AS max_parts
        FROM sets s
        JOIN themes t ON s.theme_id = t.id
        WHERE t.id = %s OR t.parent_id = %s
        """,
        (theme_id, theme_id),
        one=True,
    )
    per_year = run_query(
        """
        SELECT s.year, COUNT(*) AS set_count
        FROM sets s
        JOIN themes t ON s.theme_id = t.id
        WHERE t.id = %s OR t.parent_id = %s
        GROUP BY s.year
        ORDER BY s.year
        """,
        (theme_id, theme_id),
    )
    return {"theme": theme, "subthemes": subthemes, "stats": stats, "per_year": per_year}


@app.get("/api/stats")
def get_stats():
    totals = run_query(
        """
        SELECT
            (SELECT COUNT(*) FROM sets) AS set_count,
            (SELECT COUNT(*) FROM themes) AS theme_count,
            (SELECT MIN(year) FROM sets) AS first_year,
            (SELECT MAX(year) FROM sets) AS last_year,
            (SELECT SUM(num_parts) FROM sets) AS total_parts
        """,
        one=True,
    )
    per_year = run_query(
        """
        SELECT year, COUNT(*) AS set_count, ROUND(AVG(num_parts)) AS avg_parts
        FROM sets
        GROUP BY year
        ORDER BY year
        """
    )
    top_themes = run_query(
        """
        SELECT
            COALESCE(parent.id, t.id) AS id,
            COALESCE(parent.name, t.name) AS name,
            COUNT(*) AS set_count
        FROM sets s
        JOIN themes t ON s.theme_id = t.id
        LEFT JOIN themes parent ON t.parent_id = parent.id
        GROUP BY COALESCE(parent.id, t.id), COALESCE(parent.name, t.name)
        ORDER BY set_count DESC
        LIMIT 10
        """
    )
    biggest_sets = run_query(
        """
        SELECT s.set_num, s.name, s.year, s.num_parts, t.name AS theme_name
        FROM sets s
        LEFT JOIN themes t ON s.theme_id = t.id
        WHERE s.num_parts IS NOT NULL
        ORDER BY s.num_parts DESC
        LIMIT 10
        """
    )
    return {
        "totals": totals,
        "per_year": per_year,
        "top_themes": top_themes,
        "biggest_sets": biggest_sets,
    }


@app.get("/api/parts")
def list_parts(
    q: str = Query(default=""), limit: int = Query(default=50, ge=1, le=200)
):
    q = q.strip()
    parts = run_query(
        """
        SELECT
            p.part_num,
            p.name,
            c.name AS category_name,
            COALESCE(rc.related_count, 0) AS related_count
        FROM parts p
        JOIN part_categories c ON c.id = p.part_cat_id
        LEFT JOIN (
            SELECT part_num, COUNT(*) AS related_count
            FROM (
                SELECT child_part_num AS part_num FROM part_relationships
                UNION ALL
                SELECT parent_part_num FROM part_relationships
            ) AS ends
            GROUP BY part_num
        ) AS rc ON rc.part_num = p.part_num
        WHERE %s = '' OR p.part_num LIKE %s OR p.name LIKE %s
        ORDER BY p.part_num = %s DESC, related_count DESC, p.part_num
        LIMIT %s
        """,
        (q, f"%{q}%", f"%{q}%", q, limit),
    )
    return {"parts": parts}


@app.get("/api/parts/{part_num}")
def get_part(
    part_num: str,
    limit: int = Query(default=100, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
):
    part = run_query(
        """
        SELECT p.part_num, p.name, p.part_material, c.id AS category_id, c.name AS category_name
        FROM parts p
        JOIN part_categories c ON c.id = p.part_cat_id
        WHERE p.part_num = %s
        """,
        (part_num,),
        one=True,
    )
    if part is None:
        raise HTTPException(status_code=404, detail="Part not found")

    related = run_query(
        """
        SELECT r.rel_type, 'child' AS role, p.part_num, p.name, c.name AS category_name
        FROM part_relationships r
        JOIN parts p ON p.part_num = r.parent_part_num
        JOIN part_categories c ON c.id = p.part_cat_id
        WHERE r.child_part_num = %s
        UNION ALL
        SELECT r.rel_type, 'parent' AS role, p.part_num, p.name, c.name AS category_name
        FROM part_relationships r
        JOIN parts p ON p.part_num = r.child_part_num
        JOIN part_categories c ON c.id = p.part_cat_id
        WHERE r.parent_part_num = %s
        ORDER BY FIELD(rel_type, 'P', 'T', 'M', 'A', 'B', 'R'), role DESC, part_num
        LIMIT %s OFFSET %s
        """,
        (part_num, part_num, limit, offset),
    )
    counts = run_query(
        """
        SELECT rel_type, role, COUNT(*) AS count
        FROM (
            SELECT rel_type, 'child' AS role FROM part_relationships WHERE child_part_num = %s
            UNION ALL
            SELECT rel_type, 'parent' AS role FROM part_relationships WHERE parent_part_num = %s
        ) AS ends
        GROUP BY rel_type, role
        """,
        (part_num, part_num),
    )
    return {
        "part": part,
        "total": sum(row["count"] for row in counts),
        "limit": limit,
        "offset": offset,
        "counts": counts,
        "related": related,
    }


# ---------------------------------------------------------------------------
# Feature 3: a user's parts and the sets they can build with them.
# There is no login yet, so the frontend acts as the demo user (id 1).
# ---------------------------------------------------------------------------


class OwnedPart(BaseModel):
    part_num: str = Field(min_length=1, max_length=32)
    color_id: int
    quantity: int = Field(gt=0, le=100_000)


def require_user(user_id: int):
    user = run_query(
        "SELECT id, username FROM users WHERE id = %s", (user_id,), one=True
    )
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@app.get("/api/colors")
def list_colors():
    colors = run_query(
        """
        SELECT id, name, rgb, is_trans
        FROM colors
        -- -1 is "[Unknown]" and 9999 is "[No Color/Any Color]"; nobody owns those.
        WHERE id NOT IN (-1, 9999)
        ORDER BY name
        """
    )
    return {"colors": colors}


@app.get("/api/users/{user_id}/parts")
def list_user_parts(user_id: int):
    user = require_user(user_id)
    parts = run_query(
        """
        SELECT
            up.part_num,
            p.name AS part_name,
            up.color_id,
            c.name AS color_name,
            c.rgb,
            up.quantity
        FROM user_parts up
        JOIN parts p ON p.part_num = up.part_num
        JOIN colors c ON c.id = up.color_id
        WHERE up.user_id = %s
        ORDER BY p.name, c.name
        """,
        (user_id,),
    )
    return {"user": user, "parts": parts}


@app.post("/api/users/{user_id}/parts", status_code=204)
def add_user_part(user_id: int, part: OwnedPart):
    """Add pieces to the collection. Adding a part the user already owns increases its quantity."""
    require_user(user_id)
    try:
        run_write(
            """
            INSERT INTO user_parts (user_id, part_num, color_id, quantity)
            VALUES (%s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE quantity = quantity + VALUES(quantity)
            """,
            (user_id, part.part_num, part.color_id, part.quantity),
        )
    except HTTPException as exc:
        if exc.status_code == 404:
            raise HTTPException(status_code=400, detail="Unknown part or colour") from exc
        raise
    return Response(status_code=204)


@app.delete("/api/users/{user_id}/parts/{part_num}/{color_id}", status_code=204)
def remove_user_part(user_id: int, part_num: str, color_id: int):
    require_user(user_id)
    if run_write(
        "DELETE FROM user_parts WHERE user_id = %s AND part_num = %s AND color_id = %s",
        (user_id, part_num, color_id),
    ) == 0:
        raise HTTPException(status_code=404, detail="Part not in collection")
    return Response(status_code=204)


@app.post("/api/users/{user_id}/parts/from-set/{set_num}", status_code=204)
def add_set_parts(user_id: int, set_num: str):
    """Add every non-spare part of a set's latest inventory, e.g. for a set the user owns."""
    require_user(user_id)
    added = run_write(
        """
        INSERT INTO user_parts (user_id, part_num, color_id, quantity)
        SELECT %s, ip.part_num, ip.color_id, ip.quantity
        FROM inventories i
        JOIN inventory_parts ip ON ip.inventory_id = i.id
        WHERE i.set_num = %s
          AND ip.is_spare = 0
          AND i.version = (SELECT MAX(version) FROM inventories WHERE set_num = %s)
        ON DUPLICATE KEY UPDATE quantity = user_parts.quantity + VALUES(quantity)
        """,
        (user_id, set_num, set_num),
    )
    if added == 0:
        raise HTTPException(status_code=404, detail="Set not found or has no parts")
    return Response(status_code=204)


# Feature 3 query. A set is buildable when the user owns at least the required
# quantity of every non-spare part/colour in the set's latest inventory.
#
# Rather than checking every set, start from the user's parts: `matched` uses
# idx_inventory_parts_part_color to find each inventory that shares a
# part/colour with the collection and counts the lots the user fully covers.
# inventory_totals (precomputed at import) gives each inventory's total lots,
# so a set is buildable when lots_covered = lots. Sets with no part in common
# with the collection, or with no non-spare parts, never become candidates,
# so an empty inventory is never reported as buildable.
BUILDABLE_SQL = """
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
        WHERE o.user_id = %s
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
        s.num_parts,
        s.img_url,
        t.name AS theme_name,
        parent.name AS parent_theme_name,
        CAST(cov.pieces_required AS SIGNED) AS pieces_required,
        CAST(cov.pieces_owned AS SIGNED) AS pieces_owned,
        CAST(cov.lots_missing AS SIGNED) AS lots_missing
    FROM coverage cov
    JOIN inventories i ON i.id = cov.inventory_id
    JOIN sets s ON s.set_num = i.set_num
    LEFT JOIN themes t ON t.id = s.theme_id
    LEFT JOIN themes parent ON parent.id = t.parent_id
    WHERE i.version = (SELECT MAX(i2.version) FROM inventories i2 WHERE i2.set_num = i.set_num)
      AND {condition}
    ORDER BY {order}
    LIMIT %s
"""


@app.get("/api/users/{user_id}/buildable")
def list_buildable_sets(
    user_id: int,
    limit: int = Query(default=48, ge=1, le=200),
    almost_limit: int = Query(default=12, ge=0, le=100),
):
    user = require_user(user_id)
    buildable = run_query(
        BUILDABLE_SQL.format(
            condition="cov.lots_missing = 0",
            order="cov.pieces_required DESC, s.set_num",
        ),
        (user_id, limit + 1),
    )
    more = len(buildable) > limit
    buildable = buildable[:limit]
    almost = []
    if almost_limit:
        almost = run_query(
            BUILDABLE_SQL.format(
                condition="cov.lots_missing > 0",
                order="cov.pieces_owned / cov.pieces_required DESC, cov.lots_missing, s.set_num",
            ),
            (user_id, almost_limit),
        )
    return {"user": user, "buildable": buildable, "more": more, "almost": almost}
