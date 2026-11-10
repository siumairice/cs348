## Milestone 2

Load the full Rebrickable dataset into MySQL by default. Before this, only `themes.csv` and `sets.csv` were loaded, and then only the small `data/subset/` sample. The subset is still available for the sample queries.

### Schema (`db/schema.sql`)
- Added a table for each remaining Rebrickable CSV: `colors`, `part_categories`, `parts`, `part_relationships`, `elements`, `minifigs`, `inventories`, `inventory_parts`, `inventory_sets`, `inventory_minifigs`, `color_mappings`, `part_mappings`, and `set_mappings`.
- Added primary keys and foreign keys between them. `inventories.set_num` and `set_mappings.set_num` have no foreign key, because they can hold a set number or a minifig number (`fig-...`).
- `inventories` has a unique key on (`set_num`, `version`). `inventory_parts` has an index on (`part_num`, `color_id`) for "which sets contain this piece in this colour" queries.
- Kept the `users`, `user_parts`, and `user_completed_sets` tables from the sample database work.
- `color_mappings` uses (`color_id`, `ext_system`, `ext_id`) as its key. A color has one row per external system, so `id` alone is not unique in the full data.
- Booleans in the CSVs (`True`/`False`) are stored as `BOOLEAN`. Empty cells are stored as `NULL`.

### Importer (`db/import_data.py`, replaces `db/import_sample.py`)
- `DATA_DIR` picks the dataset: `/data` (full, the default) or `/data/subset` (sample). Compose now mounts all of `data/`.
- Loads all 15 CSVs, parent tables first: about 2.1 million rows, including 1.57 million in `inventory_parts`, in roughly 30 seconds.
- Reads each CSV as a stream and inserts it in batches of 5,000 rows, so the 134 MB `inventory_parts.csv` is never held in memory.
- Foreign key checks stay on for every table except `themes`, where a theme can reference a parent that appears later in the file.
- Skips the import when every table already has the same row count as its CSV, so restarting Compose is fast and switching `DATA_DIR` reloads. `FORCE_IMPORT=1` drops the tables and loads them again anyway.
- Never drops the user tables, so demo user data survives a reload.
- Exits with an error if a CSV is missing, has unexpected columns, or is still a Git LFS pointer.
- The `importer` Compose service now runs `python db/import_data.py`.

### README
- Updated the project description, layout, and run steps for the full dataset.
- Documented the Git LFS requirement, the import skip, `FORCE_IMPORT=1`, and how to load `data/subset/` for the sample queries.
- The sample SQL command now passes `--default-character-set=utf8mb4`, so names like "Olivia Rodrigo’s Dual Guitar" print correctly.

## Feature 4: Completed sets

Implemented Feature 4 (R9): users can mark sets as completed and manage them on a "My Completed Sets" page.

### API (`app.py`)
- Added `GET /api/completed`, which lists the demo user's completed sets, newest first. It runs the R9 query template.
- Added `POST /api/completed/{set_num}`, which runs a parameterized `INSERT` into `user_completed_sets`. `completed_at` comes from the column default (`CURRENT_TIMESTAMP`). It returns 201 with the saved row, 409 if the set is already completed (the original date is kept), and 404 if the set does not exist.
- Added `DELETE /api/completed/{set_num}`, which runs a parameterized `DELETE`. It returns `{"removed": true|false}`, so a repeated remove is harmless.
- `GET /api/sets/{set_num}` now includes `completed_at` (or `null`) for the demo user.
- Added a `run_write` helper that commits writes and maps MySQL duplicate-key and foreign-key errors to 409 and 404.
- There is no login yet. On startup the API upserts a hardcoded demo user (`sample_user`, the same user that `db/test-sample.sql` seeds) and uses its id for every request.

### Frontend (`web/`)
- The set detail page has a **Mark as Completed** button. Once a set is marked, the page shows "Completed on YYYY-MM-DD" with a **Remove** button.
- Added the **My Completed Sets** page (`/completed`) and a nav link to it. It is a table of set number, name, and completion date, with a **Remove** button per row and an empty state that links to set search.
- The buttons are plain forms backed by Next.js Server Actions (`web/app/completed/actions.ts`), so the browser still never calls FastAPI directly. The buttons disable themselves while saving, and a duplicate mark (409) counts as success.

### Sample SQL (`db/test-sample.sql`, `db/test-sample.out`)
- The demo completions now use fixed dates (two sets) instead of `CURRENT_TIMESTAMP`, so the output is the same on every run.
- Query 4 shows the newest-first ordering. After the Feature 5 query (Query 5), the script runs the "Remove" `DELETE`, and Query 6 shows the remaining set.
- Regenerated `test-sample.out` and removed a stray character from the old output.

## Feature 3: What can I build?

Users can record the parts they own and see which sets they can build with them.

### API (`app.py`)
- `GET /api/users/{id}/buildable` returns the sets a user can build: they own at least the required quantity of every non-spare part/colour in the set's latest inventory. It also returns the 12 sets the user is closest to finishing, with pieces owned, pieces required, and part/colour lots missing.
- `GET`/`POST /api/users/{id}/parts` and `DELETE /api/users/{id}/parts/{part_num}/{color_id}` list, add, and remove owned parts. Adding a part the user already owns increases its quantity. Unknown parts or colours return 400.
- `POST /api/users/{id}/parts/from-set/{set_num}` adds every non-spare part of a set, so a user can enter a set they own in one click.
- `GET /api/colors` lists colours for the add-part form, leaving out `[Unknown]` and `[No Color/Any Color]`.
- Writes use parameterized queries through the shared `run_write` helper from Feature 4.

### Query and performance
- The query starts from the user's parts instead of checking every set. It finds the inventories that share a part/colour with the collection, counts the lots the user fully covers, and compares that against each inventory's total lots. Sets with nothing in common with the collection, or with no non-spare parts, are never candidates, so an empty inventory is never reported as buildable.
- Added `inventory_totals` (lots and pieces per inventory), rebuilt by the importer from `inventory_parts` after every run (about 1 second).
- Widened `idx_inventory_parts_part_color` to (`part_num`, `color_id`, `is_spare`, `quantity`) so the part/colour lookup is answered from the index alone. This also helps feature 1.
- With a 7,499-piece collection (the Millennium Falcon's parts) on the full dataset, the endpoint went from 4.2 s to 0.3 s. Both the large collection and a small one return exactly the same sets as the report's `NOT EXISTS` query.

### Database
- `db/schema.sql` creates the demo user `sample_user` (id 1), since there is no login yet.
- On restart, the importer now also applies the schema and rebuilds `inventory_totals`, so existing volumes pick up new tables without a full reload.

### Frontend (`web/`)
- **My Parts** (`/my-parts`): add parts by number, colour, and quantity; see the collection with colour swatches; remove parts.
- **What Can I Build** (`/build`): buildable sets as cards, then "Almost there" sets with a progress bar.
- Set pages have an **I own this set** button that adds the set's parts.
- Added both pages to the nav, which now wraps on narrow screens.
- Writes go through Next.js Server Actions, so the browser still never calls the API directly.

## README (C1)

- Reorganized `README.md` around the C1 requirements, with separate sections on running the app, the sample database, and the production database.
- Added a features table covering features 1 to 5: status, where each one is in the app, and which files implement it. Feature 1 is not implemented in the app yet.
- Documented where the production data comes from, how to download it, what `db/import_data.py` checks and transforms, and the row count of every table.
- Added `db/download_data.sh`, which downloads and unzips the latest 15 Rebrickable CSVs. A fresh export imports cleanly with foreign key checks on.

## Production queries (C4)

- Added `db/test-production.sql`, which runs the app's query for features 1 to 5 on the production dataset, and `db/test-production.out`, its output. Long results show the top 10 rows plus a count of the full result.
- The script uses its own `production_user` (owns every part of Rivendell, completed two sets on fixed dates) and deletes it at the end, so the output is identical on every run and the website's demo user is untouched.
- It also runs the report's `NOT EXISTS` form of Feature 3 as a cross-check. Both forms find the same 12 buildable sets.
- Added `db/explain_production.py` and `db/test-production-plans.out`: the median time of 5 runs and the `EXPLAIN ANALYZE` plan for each query tagged `-- plan:` in `db/test-production.sql`.

| Query | Median | Plan |
| --- | ---: | --- |
| Feature 1: sets containing a part in a colour | 1.5 ms | Covering lookup on `idx_inventory_parts_part_color` (1,011 matching inventories) |
| Feature 2: count matching sets | 3.2 ms | Full scan of `sets` (28,547 rows). The theme-or-subtheme `OR` prevents index use, but the table is small |
| Feature 2: first page of matching sets | 4.9 ms | Same scan, then a sort of the 19 matches |
| Feature 3: buildable sets (app query) | 99 ms | Starts from the user's 898 lots, a covering lookup per lot, then `inventory_totals` by primary key |
| Feature 3: almost-buildable sets | 150 ms | Same plan, sorted by coverage |
| Feature 3: report's `NOT EXISTS` template | 407 ms | Scans all 1.57M `inventory_parts` rows |
| Feature 4: completed sets | 0.1 ms | Primary-key lookup on `user_completed_sets` |
| Feature 5: related parts | 0.4 ms | Lookups on the `child_part_num` and `parent_part_num` foreign key indexes |

