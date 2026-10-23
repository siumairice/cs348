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

### Next.js frontend (`web/`)
- Added a Next.js (App Router, TypeScript, Tailwind) frontend on port 3000.
- Pages: overview (`/`), set search (`/sets`), set detail (`/sets/[setNum]`), theme list (`/themes`), and theme detail (`/themes/[id]`).
- Set search filters by name/set number/theme, theme, year range, and piece range, with five sort orders and pagination. Filters live in the URL, so searches can be shared.
- Overview and theme pages show totals, a sets-per-year chart, top themes, and the biggest sets.
- `web/lib/api.ts` is a typed client for the API. Pages fetch from FastAPI on the server using `API_URL`, so the browser never calls the API directly.

### API
- `/api/sets` now accepts `theme_id` (includes direct subthemes), `year_min`, `year_max`, `parts_min`, `parts_max`, `sort`, `limit`, and `offset`, and returns a `total` count. Unknown sort values return 400.
- Added `/api/sets/{set_num}` (set, theme chain, up to 8 related sets; 404 if missing).
- Added `/api/themes` (set counts and year range per theme, optional `q`) and `/api/themes/{id}` (stats, subthemes, sets per year).
- Added `/api/stats` (catalogue totals, sets per year, top 10 themes, 10 biggest sets).
- All filter values are passed as query parameters; sort orders come from a fixed whitelist.

### Docker and fixes
- Added a `web` Compose service built from `web/Dockerfile` (Next.js standalone output), with `API_URL=http://app:8000`.
- Fixed `app.py` and the `Dockerfile` to load `index.html` from `src/` instead of the missing `templates/` folder.
- Added `web/` to `.dockerignore` so the backend image does not copy `node_modules`.
- Documented the frontend and the API endpoints in the README.

















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

### Sample SQL queries (`db/test-sample.sql`)
- Added queries to find sets containing a specified part and color, browse sets by theme and minimum part count (ordered by theme, part count, then set number), check which sets a user can build, and list a user's completed sets.

### Repository hygiene (`.gitignore`)
- Ignore local `.env` files while allowing `.env.example` to be shared safely.
- Ignore Python bytecode/cache files, common virtual-environment directories, and macOS `.DS_Store` files.
