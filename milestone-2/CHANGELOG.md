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
