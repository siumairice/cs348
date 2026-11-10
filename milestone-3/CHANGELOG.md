## Sample database setup

- Expanded `db/schema.sql` to create the Rebrickable tables needed by the sample dataset, plus `users`, `user_parts`, and `user_completed_sets`.
- Updated `db/import_sample.py` to load CSVs from `data/subset/` by default, validate input files and headers, normalize boolean values, and import rows in batches.
- Configured Compose to mount `data/subset/` for the sample import, with the full `data/` mount documented as a commented alternative.
- Updated `db/test-sample.sql` with queries and demo user data matching the Indiana Jones sample rows.
- Documented database setup, sample query execution, and the distinction between subset and full-dataset output in the README.