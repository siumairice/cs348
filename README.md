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
  schema.sql           Rebrickable tables plus users, user_parts, user_completed_sets
  import_data.py       loads the Rebrickable CSVs (full or subset) into MySQL
  test-sample.sql      sample query
  test-sample.out      expected result
src/
  index.html           plain HTML test page served by FastAPI at /
web/                   Next.js frontend (App Router, Tailwind)
  app/                 pages: overview, /sets, /sets/[setNum], /themes, /themes/[id], /parts, /parts/[partNum]
  lib/api.ts           typed client for the FastAPI endpoints
data/                  full Rebrickable CSV downloads (inventory_parts.csv uses Git LFS)
  subset/              small foreign-key-valid sample (Indiana Jones sets)
milestone-0/           contains changelog for each milestone
milestone-1/
milestone-2/
milestone-3/
```

## Prerequisites

- Docker Desktop
- Git LFS (`git lfs install && git lfs pull`), since `data/inventory_parts.csv` is stored with LFS. Not needed for the `data/subset/` sample.

## How to Run the Application

### 1. Start the containers

From the project root:

```bash
docker compose up --build
```

MySQL is initialized from `db/schema.sql`. Once the database is healthy, the importer loads every CSV in `data/` (the full dataset, about 2.1 million rows, roughly 30 seconds). The API and the Next.js frontend then start.

On later starts the importer sees the data is already loaded and exits right away. To reload anyway, for example after changing the schema:

```bash
docker compose run --rm -e FORCE_IMPORT=1 importer
```

To load the small Indiana Jones sample in `data/subset/` instead (no Git LFS needed), point `DATA_DIR` at it. Run the same command without the override to switch back to the full dataset:

```bash
docker compose run --rm -e DATA_DIR=/data/subset importer
```

The `lego_sets` database also contains `users`, `user_parts`, and `user_completed_sets`. The importer never drops these. The sample SQL script seeds a demo user and example user data before running its user-related queries.

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
| `GET /api/parts` | Search parts by number or name, with how many related parts each has. Params: `q`, `limit` (max 200) |
| `GET /api/parts/{part_num}` | One part and its related parts (prints, patterns, alternate moulds, alternates, sub-parts, pairs) with relationship type and per-group totals. Params: `limit` (default 100, max 200), `offset` |

### Frontend development

To work on the frontend with hot reload, keep the `db` and `app` containers running and start Next.js locally (Node 20+):

```bash
cd web
npm install
npm run dev
```

It reads `API_URL` (default `http://localhost:8000`). Pages fetch from FastAPI on the server, so the browser never calls the API directly.

MySQL is available on host port **3307** (mapped from container 3306) so it does not conflict with a local MySQL install.

### 3. Run the sample SQL queries

With the stack running:

```bash
docker compose exec -T db mysql -uroot -pcs348pass --default-character-set=utf8mb4 --batch --raw lego_sets < db/test-sample.sql
```

The queries match the small Indiana Jones dataset in `data/subset/`, so load it first (`docker compose run --rm -e DATA_DIR=/data/subset importer`). Compare the output to `db/test-sample.out`. The `completed_at` timestamp will differ, since the script sets it when it runs.

### 4. Stop the app

```bash
docker compose down -v
```

or Ctrl + C. Use `-v` only when you want to wipe the MySQL volume.

## Data attribution

All LEGO data comes from [Rebrickable](https://rebrickable.com/downloads/).