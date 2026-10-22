## Milestone 1

















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
