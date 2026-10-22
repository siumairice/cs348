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
templates = Jinja2Templates(directory="templates")


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={},
    )


@app.get("/api/sets")
def list_sets(q: str = Query(default="")):
    connection = None
    cursor = None
    try:
        connection = get_connection()
        cursor = connection.cursor(dictionary=True)
        pattern = f"%{q}%"
        cursor.execute(
            """
            SELECT
                s.set_num,
                s.name,
                s.year,
                s.num_parts,
                t.name AS theme_name
            FROM sets s
            LEFT JOIN themes t ON s.theme_id = t.id
            LEFT JOIN themes parent ON t.parent_id = parent.id
            WHERE %s = ''
               OR s.name LIKE %s
               OR t.name LIKE %s
               OR parent.name LIKE %s
            ORDER BY s.year DESC, s.name
            LIMIT 50
            """,
            (q, pattern, pattern, pattern),
        )
        return {"sets": cursor.fetchall()}
    except Error as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    finally:
        if cursor is not None:
            cursor.close()
        if connection is not None and connection.is_connected():
            connection.close()
