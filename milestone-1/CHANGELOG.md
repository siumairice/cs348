## Milestone 1

Turned the starter seed script into a FastAPI website with a reusable MySQL layer and real Rebrickable data.

### Website and API
- Replaced `app.py` with a FastAPI app served by Uvicorn on port 8000.
- Added `templates/index.html`, a search page that calls `/api/sets`.
- `/api/sets?q=` searches set name, theme, and parent theme and returns up to 50 rows (`num_parts` included).
- Interactive docs are at `/docs`.

### Database
- Added `database.py` with the existing retry loop and env-based MySQL settings.
- Added `db/schema.sql`: `themes` (`id`, `name`, `parent_id`) and `sets` (`set_num`, `name`, `year`, `theme_id`, `num_parts`, `img_url`).
- Added `db/import_sample.py` to load `data/themes.csv` and `data/sets.csv`. Import runs as a one-shot Compose service, not on every web request.
- Added `db/test-sample.sql` and `db/test-sample.out` for three known sets (Rivendell, Millennium Falcon, X-Wing).

### Docker
- App command is now `uvicorn app:app --host 0.0.0.0 --port 8000`, with `8000:8000` published.
- MySQL healthcheck; schema mounted into `docker-entrypoint-initdb.d`.
- Importer service mounts `data/` and must finish before the web app starts.

















## Feedback Implementation

Hardened the starter app so Compose starts cleanly after a volume wipe and does not collide with a local MySQL install.

### MySQL connection retry (`app.py`)
- Replaced the fixed 10-second wait with a retry loop: up to 30 attempts, 2 seconds apart.
- After `docker compose down -v`, MySQL can finish a cold start before the app gives up.
- If the connection never succeeds, the script prints the error and exits with code 1.

### Host port mapping (`docker-compose.yml`)
- Mapped host port `3307` to container port `3306` so a local MySQL on 3306 does not block `docker compose up`.
- The app still connects to `db:3306` inside Docker. Use port 3307 from the host.

### Schema cleanup (`app.py`)
- Removed `DROP TABLE IF EXISTS users` on every run so a future `users` table is not wiped.
