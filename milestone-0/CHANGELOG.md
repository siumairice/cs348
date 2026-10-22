## Milestone 0 — starter code

Set up a Dockerized Python + MySQL app that creates a small LEGO schema, seeds sample data, and prints a join query.

### Repo layout
- Added a root `README.md` with run instructions (`docker compose up --build`, expected output, `docker compose down -v`).
- Added empty `milestone-0` through `milestone-3` folders for per-milestone notes.

### Docker
- Added `Dockerfile` (Python 3.11, installs `requirements.txt`, runs `app.py`).
- Added `docker-compose.yml` with:
  - `db`: MySQL 8.0, root password `cs348pass`, database `lego_sets`, named volume for data.
  - `app`: builds from the Dockerfile and depends on `db`.
- Added `requirements.txt` with `mysql-connector-python`.

### Database and seed script (`app.py`)
- Connects to MySQL as root using the Compose service name `db`.
- Creates `themes` (`id`, `name`) and `sets` (`set_num`, `name`, `year`, `theme_id` with a foreign key to `themes`).
- Clears existing rows, then seeds:
  - themes: Star Wars, Icons
  - sets: X-Wing Starfighter (2023), Millennium Falcon (2017), Rivendell (2023)
- Runs an `INNER JOIN` of sets to themes, ordered by year descending, and prints the rows.
- Closes the cursor and connection after the run.
