# CS348 Project

LEGO Sets Explorer: a FastAPI website backed by MySQL, using Rebrickable set and theme data.

## Organization

The application lives in the project root. Milestone folders contain changelogs for that milestone.

```text
app.py                 FastAPI routes and HTML page
database.py            MySQL connection and retry logic
requirements.txt
Dockerfile
docker-compose.yml
db/
  schema.sql           themes and sets tables
  import_sample.py     loads Rebrickable CSVs into MySQL
  test-sample.sql      sample query
  test-sample.out      expected result
templates/
  index.html           search page
data/                  Rebrickable CSV downloads
```

## Prerequisites

- Docker Desktop

## How to Run the Application

### 1. Start the containers

From the project root:

```bash
docker compose up --build
```

MySQL is initialized from `db/schema.sql`. The importer loads Rebrickable themes and sets once the database is healthy. The web app then starts.

### 2. Open the website

- Website: http://localhost:8000
- Search API: http://localhost:8000/api/sets
- Search example: http://localhost:8000/api/sets?q=Star%20Wars
- API docs: http://localhost:8000/docs

MySQL is available on host port **3307** (mapped from container 3306) so it does not conflict with a local MySQL install.

### 3. Run the sample SQL test

With the stack running:

```bash
docker compose exec -T db mysql -uroot -pcs348pass --table lego_sets < db/test-sample.sql
```

Compare the output to `db/test-sample.out`.

### 4. Stop the app

```bash
docker compose down -v
```

or Ctrl + C. Use `-v` only when you want to wipe the MySQL volume.

## Data attribution

Set and theme data comes from [Rebrickable](https://rebrickable.com/downloads/).