## Sample database setup

- Expanded `db/schema.sql` to create the Rebrickable tables needed by the sample dataset, plus `users`, `user_parts`, and `user_completed_sets`.
- Updated `db/import_sample.py` to load CSVs from `data/subset/` by default, validate input files and headers, normalize boolean values, and import rows in batches.
- Configured Compose to mount `data/subset/` for the sample import, with the full `data/` mount documented as a commented alternative.
- Updated `db/test-sample.sql` with queries and demo user data matching the Indiana Jones sample rows.
- Documented database setup, sample query execution, and the distinction between subset and full-dataset output in the README.

## Similar parts (Feature 5)

- Added `GET /api/parts` to search parts by number or name. Each result includes how many related parts it has, and an exact part-number match is listed first.
- Added `GET /api/parts/{part_num}`, which returns a part and its related parts from `part_relationships` (prints, patterns, alternate moulds, alternates, sub-parts, pairs), together with the relationship type and which side of the relationship the requested part is on. Results are paginated with `limit`/`offset` and include the total and a count per relationship group.
- Added `/parts` (search) and `/parts/[partNum]` (related parts grouped by relationship) pages to the frontend, plus a Parts link in the nav. Clicking a row opens that part. The detail page shows 100 related parts per page (`?page=N`).
- Added the related-parts query for part 2339 to `db/test-sample.sql` and its subset output to `db/test-sample.out`.
- Documented the new endpoints in the README.
