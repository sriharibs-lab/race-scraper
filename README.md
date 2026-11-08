# race-scraper

A Python script that pulls every upcoming running race in Washington, Oregon and California from the RunSignUp API and publishes them as one flat `races.json`. It is the data backbone for [Run Down](https://github.com/sriharibs-lab/run-down), my race-finder app.

Not deployed as a service. The data lives in this repo and is refreshed by a GitHub Action every night at 10:00 UTC (02:00 PST, 03:00 PDT). The latest `races.json` is always at `https://raw.githubusercontent.com/sriharibs-lab/race-scraper/main/races.json`.

## What it does

- Fetches every race RunSignUp lists in WA, OR and CA, with their events (distances).
- Flattens one race with N events into N rows, so a 5K and a half marathon at the same event are separate entries.
- Drops races whose next date has passed; keeps rows with unknown or unparseable dates.
- Attaches an image to every row: the race's own RunSignUp logo when it has one, a fixed Unsplash running photo when it doesn't.
- Tags each row with a difficulty bucket and a `hasKidsRace` flag derived from event names.
- Writes a single `races.json` (5,153 rows, 19 MB as of the last run) that downstream apps fetch over raw GitHub.

## How it works

One class, `RunSignUpRaceFetcher`, does everything in `fetch_races.py`. For each of the three states it walks the paginated `GET https://api.runsignup.com/rest/races` endpoint with `format=json`, `events=T`, `results_per_page=50`, incrementing `page` until the API returns an empty `races` array. Each race is unwrapped from its `{"race": {...}}` envelope, split into one row per event, filtered to future dates and dumped to `races.json`. There is no database, no API key and no server.

Every night GitHub Actions runs the script on `ubuntu-latest` and commits `races.json` back to `main` if it changed. One hour later, a second Action in `sriharibs-lab/run-down` curls that raw file into its `src/data/races.json` and commits it, so the app redeploys with fresh data without the two repos sharing any code.

```
                 ┌──────────────────────────────┐
  02:00 PST      │  race-scraper (this repo)     │
  cron 0 10 UTC  │  .github/workflows/           │
                 │    fetch-races.yml            │
                 │                               │
   RunSignUp     │  for state in WA, OR, CA:     │
   REST API ───▶ │    page 1..N (50/page) ──┐    │
                 │                          ▼    │
                 │    unwrap race ─▶ 1 row/event │
                 │    ─▶ difficulty, kids flag   │
                 │    ─▶ logo_url or Unsplash    │
                 │    ─▶ drop past dates         │
                 │                          │    │
                 │    races.json ◀──────────┘    │
                 │    git commit + push          │
                 └──────────────┬───────────────┘
                                │ raw.githubusercontent.com
  03:00 PST                     ▼
  cron 0 11 UTC  ┌──────────────────────────────┐
                 │  run-down                     │
                 │  .github/workflows/           │
                 │    update-races.yml           │
                 │  curl ─▶ src/data/races.json  │
                 │  git commit + push            │
                 └──────────────────────────────┘
```

### Output schema

Every row in `races.json` has exactly these 13 keys (`transform_race_data` in `fetch_races.py`):

| key | type | source |
| --- | --- | --- |
| `id` | string | `"{race_id}_{event_id}"`, or just `race_id` when the race has no events |
| `name` | string | race name |
| `date` | string `MM/DD/YYYY` | RunSignUp `next_date` |
| `city` | string | `address.city` |
| `state` | `"WA" \| "OR" \| "CA"` | the state the page was fetched for |
| `distance` | string or null | event `distance`, e.g. `"5K"`, `"13.1 Miles"` |
| `difficulty` | string | `Beginner`, `Easy`, `Moderate`, `Hard`, `Expert`, `Extreme` |
| `description` | string | race description, raw HTML from RunSignUp |
| `imageUrl` | string | race `logo_url` or the Unsplash fallback |
| `latitude`, `longitude` | number | currently always `0.0` (see Status) |
| `hasKidsRace` | boolean | any event name contains kids/children/family/youth/junior |
| `registrationUrl` | string | RunSignUp race URL |

## Craft notes

- **Pagination stops on empty, not on a count.** The API is walked at 50 results per page until it returns an empty `races` array, with a `0.5 s` sleep between pages (`fetch_races.py`). The last run in the log (2025-10-10) requested 8 pages for WA, 4 for OR and 25 for CA (the final page of each is the empty one that stops the loop) and took 40 seconds end to end for 5,567 raw rows (`race_fetcher.log`).
- **Images: RunSignUp logo first, Unsplash only as a constant fallback.** The first version queried the Unsplash search API for a `"{city} {state} skyline"` photo per race, gated on `UNSPLASH_ACCESS_KEY`. I replaced that on 2025-09-18 (commit `a10c4de`) with the race's own `logo_url`; the script now makes zero Unsplash API calls and needs no key. In the current data 4,967 of 5,153 rows carry a RunSignUp-hosted logo (`d368g9lw5ileu7.cloudfront.net`) and 186 fall back to one hard-coded Unsplash photo (`races.json`).
- **One row per event, not per race.** 1,339 distinct races expand to 5,153 rows so the app can filter by distance without re-parsing events (`races.json`). A race with no events still produces one row with `distance: "Unknown"` (`fetch_races.py`).
- **Date filter fails open.** `filter_future_races` parses `MM/DD/YYYY` and keeps anything from today forward, but a missing or unparseable date is kept rather than dropped, so a bad upstream value never silently removes a race (`fetch_races.py`). The last run kept 4,897 of 5,567 rows (`race_fetcher.log`).
- **Difficulty is substring matching on the distance string**, checked in order Beginner → Easy → Moderate → Hard → Expert → Extreme, defaulting to `Moderate` (`fetch_races.py`). It is wrong today: `"13.1 Miles"` matches the Beginner token `1 mile` and `"26.2 Miles"` matches the Moderate token `6.2`, so all 469 half marathons are `Beginner` and all 78 marathons are `Moderate` in the current file (`races.json`). Noted under Status.
- **Nightly job commits only when the diff is non-empty**, using `git diff --quiet && git diff --staged --quiet || (commit && push)` so quiet nights do not add commits (`.github/workflows/fetch-races.yml`). The downstream run-down job uses the same guard (`run-down/.github/workflows/update-races.yml`).
- **Request hygiene:** a persistent `requests.Session` with a desktop User-Agent, 30 s timeout per page, and a failed page ends that state's walk instead of crashing the run (`fetch_races.py`).

## Run locally

```bash
pip install -r requirements.txt
python fetch_races.py
```

Writes `races.json` and `race_fetcher.log` in the working directory. No environment variables are required. `UNSPLASH_ACCESS_KEY` is no longer read.

To trigger the nightly job by hand, run the "Fetch Race Data" workflow from the Actions tab (`workflow_dispatch`).

## Status / roadmap

Working and running nightly since 2025-09-18. Last data commit in this checkout is 2026-10-30.

Known gaps, in the order I would fix them:

- `latitude` and `longitude` are `0.0` on every row. The script reads them from the top level of the race object; RunSignUp returns them inside `address`.
- Difficulty mis-buckets half marathons and marathons (see Craft notes). Needs ordered, anchored matching instead of substrings.
- 969 rows have `distance: null` and land in `Moderate` by default.
- `description` is raw HTML; the consumer has to sanitize it.
- The log file was tracked in git until this cleanup. It is now ignored.

## License

MIT. See [LICENSE](LICENSE).
