from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from mysql.connector import Error

from database import connect_with_retry, get_connection

@asynccontextmanager
async def lifespan(app: FastAPI):
    connection = connect_with_retry()
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


@app.get("/", response_class=HTMLResponse)
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
    return {"set": row, "related": related}


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
