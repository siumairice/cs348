## Milestone 2

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
- Query 4 shows the newest-first ordering. Then the script runs the "Remove" `DELETE`, and Query 5 shows the remaining set.
- Regenerated `test-sample.out` and removed a stray character from the old output.
