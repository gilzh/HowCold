# HowCold

Daily scheduled task fetches water/air temperature (`node fetch.js`) and appends
a row to `temperatures.csv`.

## Publishing the daily update

The live site (`index.html`) reads `temperatures.csv` directly from the `main`
branch via `fetch()`. After committing the daily update to the assigned
feature/dev branch, merge that branch into `main` (fast-forward) and push
`main` as well, so the site picks up the new row same-day. This merge is
pre-authorized — no need to ask before doing it, per the user's standing
instruction (2026-09-12).
