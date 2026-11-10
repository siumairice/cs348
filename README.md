# CS348 Project

LEGO Sets Explorer: a Next.js frontend and FastAPI backend over MySQL, built on the [Rebrickable](https://rebrickable.com/downloads/) LEGO dataset (sets, themes, parts, colours, minifigs, and inventories). Users can browse sets, look up parts, record the pieces they own, see which sets they can build, and track the sets they have completed.

## Contents

- [Features](#features)
- [Prerequisites](#prerequisites)
- [Run the application](#run-the-application)
- [Sample database](#sample-database)
- [Production database](#production-database)
- [API endpoints](#api-endpoints)
- [Project layout](#project-layout)

## Features

Feature numbers match the report (R6 to R10). All five are implemented.

| # | Feature | Status | Where in the app | Implementation |
| --- | --- | --- | --- | --- |
| 1 (R6) | Find sets that contain a given part in a given colour | Implemented | **Find Sets** (`/find-sets`): enter a part number, pick one of the colours it comes in, and see the sets, newest first. Also linked from each part's page | `list_part_colors`, `list_sets_with_part` in `app.py`; `web/app/find-sets/page.tsx` |
| 2 (R7) | Search sets by theme and piece count | Implemented | **Sets** (`/sets`): theme drop-down, min/max pieces, year range, name search, sorting, pagination | `list_sets` in `app.py`; `web/app/sets/page.tsx` |
| 3 (R8) | Find sets the user can build with their pieces | Implemented | **My Parts** (`/my-parts`) to enter pieces, or **I own this set** on a set page; **What Can I Build** (`/build`) for buildable and nearly buildable sets | `list_user_parts`, `add_user_part`, `remove_user_part`, `add_set_parts`, `list_buildable_sets`, and `BUILDABLE_SQL` in `app.py`; `inventory_totals` in `db/schema.sql`; `web/app/my-parts/`, `web/app/build/page.tsx` |
| 4 (R9) | Mark sets as completed and list them | Implemented | **Mark as Completed** / **Remove** on a set page; **My Completed Sets** (`/completed`) | `list_completed`, `mark_completed`, `remove_completed` in `app.py`; `web/app/completed/` |
| 5 (R10) | Find related parts (prints, patterns, alternate moulds, alternates, sub-parts, pairs) | Implemented | **Parts** (`/parts`) to search, then a part's page (`/parts/[partNum]`) | `list_parts`, `get_part` in `app.py`; `web/app/parts/` |

The app also has an overview page with catalogue statistics (`/`), set detail pages (`/sets/[setNum]`), and theme pages (`/themes`, `/themes/[id]`).

There is no login yet. The website acts as a single demo user, `sample_user` (id 1), which `db/schema.sql` creates and the API also makes sure exists on startup.

## Prerequisites

- Docker Desktop
- Git LFS (`git lfs install && git lfs pull`), because `data/inventory_parts.csv` is stored with LFS. It is not needed for the sample database, or if you download the production data yourself (see [Production database](#production-database)).

## Run the application

From the project root:

```bash
docker compose up --build
```

This starts four containers:

1. `db`: MySQL 8.0. On a new volume it runs `db/schema.sql`, which creates the tables and the demo user.
2. `importer`: runs `db/import_data.py` once the database is healthy, loading the production dataset from `data/` (see below), then exits.
3. `app`: the FastAPI backend, started after the importer finishes.
4. `web`: the Next.js frontend.

Then open:

- Frontend: http://localhost:3000
- API docs (interactive): http://localhost:8000/docs
- Plain HTML test page: http://localhost:8000

MySQL is also reachable from the host on port **3307** (mapped from 3306 in the container), so it does not conflict with a local MySQL install.

To stop the app, press Ctrl + C or run `docker compose down`. Add `-v` to also delete the MySQL volume, so the next start rebuilds the database from scratch.

### Frontend development

To work on the frontend with hot reload, keep the `db` and `app` containers running and start Next.js locally (Node 20+):

```bash
cd web
npm install
npm run dev
```

It reads `API_URL` (default `http://localhost:8000`). Pages fetch from FastAPI on the server, and writes go through Next.js Server Actions, so the browser never calls the API directly.

## Sample database

The sample database is a small, hand-picked, foreign-key-valid subset of Rebrickable in `data/subset/`: two Indiana Jones sets, with exactly the themes, parts, colours, minifigs, and inventory rows they need (one to four rows per table). It is small enough to check query results by hand.

**Create and load it.** With the stack running (`docker compose up --build`), load the subset in place of the full data:

```bash
docker compose run --rm -e DATA_DIR=/data/subset importer
```

The tables come from `db/schema.sql`, which is the same for both datasets. The importer replaces the Rebrickable tables but keeps the `users`, `user_parts`, and `user_completed_sets` tables.

**Run the sample queries.** `db/test-sample.sql` seeds example user data, then runs the query for each feature:

```bash
docker compose exec -T db mysql -uroot -pcs348pass --default-character-set=utf8mb4 --batch --raw lego_sets < db/test-sample.sql
```

Compare the output with `db/test-sample.out`. `--default-character-set=utf8mb4` makes names with curly quotes, such as "Olivia Rodrigo’s Dual Guitar", print correctly.

**Switch back to the production data.** Running the importer without the override reloads `data/`:

```bash
docker compose run --rm importer
```

## Production database

The production database is the complete Rebrickable export: 15 CSV files and about 2.1 million rows.

### Where the data comes from

Rebrickable publishes the files at https://rebrickable.com/downloads/ (direct links: `https://cdn.rebrickable.com/media/downloads/<table>.csv.gz`) and regenerates them daily. The repo includes a snapshot in `data/`, with the 134 MB `inventory_parts.csv` stored through Git LFS.

### How to generate it

To download the latest export instead of using the snapshot:

```bash
db/download_data.sh          # downloads and unzips all 15 files into data/
```

`db/download_data.sh [destination]` can also write somewhere else. The newest export has slightly more rows than the snapshot. The table below shows the snapshot's counts.

### How to load it

`docker compose up --build` loads `data/` automatically. To force a reload, for example after downloading new files or changing the schema:

```bash
docker compose run --rm -e FORCE_IMPORT=1 importer
```

`db/import_data.py` does the extract, transform, and load:

- **Checks** that all 15 files exist, that each header has the expected columns, and that no file is still a Git LFS pointer. It stops with a clear message otherwise.
- **Transforms** each row: `True`/`False` become booleans, empty cells become `NULL`, numeric columns become integers, and `color_mappings.csv`'s `id` column is renamed to `color_id`.
- **Loads** tables parent-first, streaming each CSV in batches of 5,000 rows, with foreign key checks on. The only exception is `themes`, which references itself. The inserts run in one transaction, and the whole load takes about 30 seconds.
- **Derives** `inventory_totals` (part/colour lots and pieces per inventory) from `inventory_parts`. Feature 3 uses it.
- **Skips** the import on later starts when every table already has the same row count as its CSV, so restarts are quick. Switching `DATA_DIR` or downloading a newer export changes the counts and triggers a reload. Use `FORCE_IMPORT=1` to reload anyway.

| Table | Rows (snapshot) |
| --- | ---: |
| `inventory_parts` | 1,567,464 |
| `part_mappings` | 183,131 |
| `elements` | 114,671 |
| `set_mappings` | 71,742 |
| `parts` | 64,906 |
| `inventories` | 47,793 |
| `inventory_totals` (derived) | 39,117 |
| `part_relationships` | 37,543 |
| `sets` | 28,547 |
| `inventory_minifigs` | 25,906 |
| `minifigs` | 17,293 |
| `inventory_sets` | 5,217 |
| `color_mappings` | 846 |
| `themes` | 496 |
| `colors` | 275 |
| `part_categories` | 76 |

### Production queries

`db/test-production.sql` runs the app's query for each feature on the production dataset, with fixed inputs and the top 10 rows of long results, plus a count of the full result. It creates a separate `production_user` (who owns every part of Rivendell, 10316-1, and has completed two sets), so the website's demo user is not touched, and removes it at the end so it can be re-run. With the production data loaded:

```bash
docker compose exec -T db mysql -uroot -pcs348pass --default-character-set=utf8mb4 --table lego_sets < db/test-production.sql
```

Compare the output with `db/test-production.out`.

Query plans and timings (median of 5 runs, plus `EXPLAIN ANALYZE`) for the same queries are in `db/test-production-plans.out`. `db/explain_production.py` regenerates them. It reads the queries tagged `-- plan:` in `db/test-production.sql`, so the timed queries are always the ones in the test file:

```bash
docker compose up -d --build app   # the app image holds a copy of db/, so rebuild after editing the SQL
docker compose exec -T app python db/explain_production.py > db/test-production-plans.out
```

One mismatch in the data: about 17,000 rows in `inventories` (and some in `set_mappings`) belong to minifigs (`fig-...`) rather than sets. Their `set_num` column therefore has no foreign key to `sets`. Feature queries join `inventories` to `sets`, which leaves the minifig rows out.

## API endpoints

| Endpoint | Description |
| --- | --- |
| `GET /api/sets` | Search sets. Params: `q`, `theme_id` (includes direct subthemes), `year_min`, `year_max`, `parts_min`, `parts_max`, `sort` (`year_desc`, `year_asc`, `parts_desc`, `parts_asc`, `name`), `limit` (max 200), `offset` |
| `GET /api/sets/{set_num}` | One set with its theme chain and up to 8 related sets |
| `GET /api/themes` | All themes with set counts and year range. Param: `q` |
| `GET /api/themes/{id}` | Theme stats, subthemes, and sets per year |
| `GET /api/stats` | Catalogue totals, sets per year, top themes, biggest sets |
| `GET /api/parts` | Search parts by number or name, with how many related parts each has. Params: `q`, `limit` (max 200) |
| `GET /api/parts/{part_num}` | One part and its related parts (prints, patterns, alternate moulds, alternates, sub-parts, pairs) with relationship type and per-group totals. Params: `limit` (default 100, max 200), `offset` |
| `GET /api/completed` | The demo user's completed sets, newest first |
| `POST /api/completed/{set_num}` | Mark a set as completed today (409 if already completed, 404 if no such set) |
| `DELETE /api/completed/{set_num}` | Remove a completed set. Returns `{"removed": true\|false}` |
| `GET /api/parts/{part_num}/colors` | Feature 1: the colours a part comes in, with the number of sets using it in each colour. 404 for an unknown part |
| `GET /api/parts/{part_num}/sets` | Feature 1: sets containing the part in a colour, newest first, spares excluded. Params: `color_id` (required), `limit` (default 48, max 200), `offset`. 404 for an unknown part or colour |
| `GET /api/colors` | All colours a user can own, for the My Parts form |
| `GET /api/users/{id}/parts` | A user's parts with part name, colour name, and quantity |
| `POST /api/users/{id}/parts` | Add pieces. JSON body `{part_num, color_id, quantity}`. Adding a part the user already owns increases its quantity. 400 for an unknown part or colour |
| `DELETE /api/users/{id}/parts/{part_num}/{color_id}` | Remove one part/colour from the collection |
| `POST /api/users/{id}/parts/from-set/{set_num}` | Add every non-spare part of a set's latest inventory (for a set the user owns) |
| `GET /api/users/{id}/buildable` | Feature 3: sets the user can build with their parts, plus the closest sets they can't build yet. Params: `limit` (default 48, max 200), `almost_limit` (default 12) |

## Project layout

```text
app.py                 FastAPI routes (all features)
database.py            MySQL connection and retry logic
requirements.txt       Python dependencies
Dockerfile             backend and importer image
docker-compose.yml     db, importer, app, web services
db/
  schema.sql           tables, keys, CHECK constraints, indexes, demo user (sample and production)
  import_data.py       validates, transforms, and loads the CSVs; builds inventory_totals
  download_data.sh     downloads the latest production CSVs from Rebrickable
  test-sample.sql      one query per feature, for the sample database
  test-sample.out      expected output of test-sample.sql on the sample database
  test-production.sql  the feature queries on the production dataset
  test-production.out  output of test-production.sql
  explain_production.py         times test-production.sql's queries and records their plans
  test-production-plans.out     timings and EXPLAIN ANALYZE plans on the production dataset
src/
  index.html           plain HTML test page served by FastAPI at /
web/                   Next.js frontend (App Router, TypeScript, Tailwind)
  app/                 pages: /, /sets, /sets/[setNum], /themes, /themes/[id], /parts,
                       /parts/[partNum], /find-sets, /my-parts, /build, /completed
  lib/api.ts           typed client for the FastAPI endpoints
data/                  production dataset snapshot (inventory_parts.csv uses Git LFS)
  subset/              sample dataset
milestone-0/ ... milestone-3/   changelog for each milestone
```

## Data attribution

All LEGO data comes from [Rebrickable](https://rebrickable.com/downloads/).
