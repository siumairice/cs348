# CS348 Project

LEGO Sets Explorer: a Next.js frontend and FastAPI backend over MySQL, using the full Rebrickable dataset (sets, themes, parts, colors, minifigs, and inventories).

## Organization

The application lives in the project root. Milestone folders contain changelogs for that milestone.

```text
app.py                 FastAPI routes and HTML page
database.py            MySQL connection and retry logic
requirements.txt
Dockerfile
docker-compose.yml
db/
  schema.sql           tables for every Rebrickable CSV
  import_data.py       loads all Rebrickable CSVs into MySQL
  test-sample.sql      sample query
  test-sample.out      expected result
src/
  index.html           plain HTML test page served by FastAPI at /
web/                   Next.js frontend (App Router, Tailwind)
  app/                 pages: overview, /sets, /sets/[setNum], /themes, /themes/[id]
  lib/api.ts           typed client for the FastAPI endpoints
data/                  Rebrickable CSV downloads (inventory_parts.csv uses Git LFS)
milestone-0/           contains changelog for each milestone
milestone-1/
milestone-2/
milestone-3/
```

## Prerequisites

- Docker Desktop
- Git LFS (`git lfs install && git lfs pull`), since `data/inventory_parts.csv` is stored with LFS

## How to Run the Application

### 1. Start the containers

From the project root:

```bash
docker compose up --build
```

MySQL is initialized from `db/schema.sql`. Once the database is healthy, the importer loads every CSV in `data/` (about 2.1 million rows, roughly 30 seconds). The API and the Next.js frontend then start.

On later starts the importer sees the data is already loaded and exits right away. To reload after changing the CSVs or the schema:

```bash
docker compose run --rm -e FORCE_IMPORT=1 importer
```

### 2. Open the website

- Frontend: http://localhost:3000
- API docs: http://localhost:8000/docs
- Plain test page: http://localhost:8000

API endpoints:

| Endpoint | Description |
| --- | --- |
| `GET /api/sets` | Search sets. Params: `q`, `theme_id` (includes direct subthemes), `year_min`, `year_max`, `parts_min`, `parts_max`, `sort` (`year_desc`, `year_asc`, `parts_desc`, `parts_asc`, `name`), `limit` (max 200), `offset` |
| `GET /api/sets/{set_num}` | One set with its theme chain and up to 8 related sets |
| `GET /api/themes` | All themes with set counts and year range. Param: `q` |
| `GET /api/themes/{id}` | Theme stats, subthemes, and sets per year |
| `GET /api/stats` | Catalogue totals, sets per year, top themes, biggest sets |

### Frontend development

To work on the frontend with hot reload, keep the `db` and `app` containers running and start Next.js locally (Node 20+):

```bash
cd web
npm install
npm run dev
```

It reads `API_URL` (default `http://localhost:8000`). Pages fetch from FastAPI on the server, so the browser never calls the API directly.

MySQL is available on host port **3307** (mapped from container 3306) so it does not conflict with a local MySQL install.

### 3. Run the sample SQL test

With the stack running:

```bash
docker compose exec -T db mysql -uroot -pcs348pass --default-character-set=utf8mb4 --batch --raw lego_sets < db/test-sample.sql
```

Compare the output to `db/test-sample.out`.

### 4. Stop the app

```bash
docker compose down -v
```

or Ctrl + C. Use `-v` only when you want to wipe the MySQL volume.

## Data attribution

All LEGO data comes from [Rebrickable](https://rebrickable.com/downloads/).