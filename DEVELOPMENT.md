# Development guide

Technical documentation for `awesome-codeswissgov` — installation, commands,
contributing, architecture, and testing.

This guide is the practical "how to work with the repo" reference. For the
*what* and *why*, see [`SPEC.md`](./SPEC.md) (the buildable contract) and
[`DESIGN.md`](./DESIGN.md) (strategy and rationale).

---

## Architecture overview

`data/orgs/*.yaml` is the **source of truth** — one curated file per
organization. `README.md` (the federal + cantonal tables) and `inventory.json`
are **generated views**, never edited by hand:

```
data/orgs/*.yaml ── build ──▶ README.md tables
                          └─▶ inventory.json
                 ── harvest ─▶ inventory.json (repo-level data)
```

Because the views are regenerated from `data/orgs/` every time, there is no
manual two-way sync to drift and orphaned rows cannot occur. `validate` (the CI
gate) fails if the committed views are out of date.

## Project structure

```
src/codeswissgov/
  __main__.py        → CLI dispatch (build | validate | harvest | ingest | check | report)
  models.py          → pydantic models: Organization, Repository
  loader.py          → load + validate data/orgs/*.yaml
  build.py           → render_all / build / validate
  cantons.py         → 26-canton code ⇄ display-name reference map
  orgurl.py          → GitHub org-URL helpers (org_login, login_key)
  render/
    __init__.py      → deterministic ordering (federal / cantonal)
    readme.py        → data/orgs → README tables (between markers)
    inventory.py     → data/orgs (+ harvest) → inventory.json
    reports.py       → license / staleness / coverage / EMBAG reports (pure)
  harvest/
    __init__.py      → run_harvest orchestration
    github.py        → GitHub GraphQL client
  ingest/
    __init__.py      → run_ingest orchestration
    registry.py      → Candidate model, RegistrySource, reconcile, render_report
    swiss_index.py   → swiss/index registry source
  check/
    __init__.py      → run_check orchestration + fetch_status (HTTP)
    linkrot.py       → classify + build_report + render_report (pure)
data/orgs/*.yaml     → SOURCE OF TRUTH (curated, git-tracked)
tests/               → pytest unit + fixture-based tests
  fixtures/          → recorded API / registry responses
.github/workflows/
  ci.yml             → lint + test + validate (sync gate) on PR/push
  harvest.yml        → scheduled harvest + auto-PR
README.md            → GENERATED VIEW (do not hand-edit the tables)
inventory.json       → GENERATED data product
SPEC.md  DESIGN.md   → contract + rationale
```

## Installation

Python 3.11+.

```sh
pip install -e . -r requirements-dev.txt
```

Runtime deps (`requirements.txt`): `PyYAML`, `httpx`, `pydantic` v2.
Dev deps (`requirements-dev.txt`): `pytest`, `pytest-httpx`, `ruff`.

## Commands

All commands run as `python -m codeswissgov <command>`.

| Command | Purpose |
|---------|---------|
| `build` | Regenerate `README.md` tables + `inventory.json` from `data/orgs/`. |
| `validate` | Schema-check `data/orgs/` **and** assert the generated views are up to date (the CI gate). |
| `harvest` | Enrich `inventory.json` with repo-level data from the GitHub API. |
| `ingest` | Reconcile sibling registries (`swiss/index`) against `data/orgs/`; print a read-only report. |
| `check` | Detect link rot in the curated org URLs (404 / renamed); print a read-only report. |
| `report` | Print license / staleness / authority-coverage / EMBAG reports from `data/orgs` + `inventory.json`. |

```sh
python -m codeswissgov build
python -m codeswissgov validate
python -m codeswissgov harvest --token "$GITHUB_TOKEN"   # or $GITHUB_TOKEN in env
python -m codeswissgov ingest                            # no token needed
python -m codeswissgov check                             # no token needed
python -m codeswissgov report                            # no token needed
```

## Contributing

To add or update an organization:

1. Add or edit a file under `data/orgs/`, named after the GitHub handle, e.g.
   `data/orgs/<github-handle>.yaml`:
   ```yaml
   name: Statistics I            # display name (service for federal; unit for cantonal)
   authority: canton:ZH          # "federal" or "canton:<CODE>" (e.g. canton:BE)
   url: https://github.com/statistikstadtzuerich
   official: false               # true only with recorded provenance (see below)
   provenance: null              # evidence source backing `official`
   ```
   A canton with no known GitHub org needs **no** file — the build renders
   `— none known yet` for it automatically.
2. Regenerate the views:
   ```sh
   pip install -e .
   python -m codeswissgov build
   ```
   The build is deterministic and self-cleaning (orphan rows cannot occur —
   the tables are rebuilt from `data/orgs/` every time).
3. Commit the `data/orgs/` change **and** the regenerated `README.md` and
   `inventory.json`.

## Data model & schema

**`Organization`** (curated, in `data/orgs/*.yaml`):

| Field | Type | Notes |
|-------|------|-------|
| `name` | str | Display name (service for federal; unit for cantonal). |
| `authority` | str | `"federal"` or `"canton:<CODE>"` (e.g. `canton:ZH`). |
| `url` | str | GitHub organization URL (only GitHub is in scope). |
| `official` | bool | Verified-official flag; defaults `false`. |
| `provenance` | str \| null | Evidence backing `official`. |

`official: true` is only permitted with a non-empty `provenance` (a registry
listing, a GitHub verified-domain match, or explicit confirmation); otherwise
the entry is an unverified candidate.

**`Repository`** (harvested, in `inventory.json` only — never in `data/orgs`):
`name`, `url`, `license` (SPDX id; `null` = compliance flag), `language`,
`topics`, `archived`, `last_activity` (ISO-8601 date), `has_publiccode_yml`,
`has_security_md`.

**`inventory.json`** (`schema_version: "2.0"`): an `organizations` array; each
entry carries the org fields plus `harvested_at` and a nested `repositories`
array. Output is canonical (stable order, two-space indent, trailing newline,
non-ASCII preserved) so diffs stay clean.

## Repository-level data (harvest)

`inventory.json` carries harvested repo-level data per organization. It is
produced from the GitHub **GraphQL** API with a read-only fine-grained PAT (to
lift the rate limit); the harvest is incremental and **cache-backed** —
`inventory.json` is itself the cache, so an org whose fetch fails keeps its
prior repositories rather than being dropped.

```sh
python -m codeswissgov harvest --token "$GITHUB_TOKEN"
```

`harvest` is the only writer of repo-level data; `build` preserves it when it
regenerates the views.

## Ecosystem interop (ingest)

The federal org list is meant to track the upstream
[`swiss/index`](https://github.com/swiss/index) registry. `ingest` reconciles
that registry (via a pluggable `RegistrySource` framework) against `data/orgs/`
and prints a **read-only** report — it never edits `data/orgs/`:

```sh
python -m codeswissgov ingest        # no token needed (public registry)
```

The report lists orgs present in a registry but **missing** from `data/orgs/`
(the coverage gap to review), with a federal/cantonal hint from the registry's
section. It is guidance only: a maintainer decides what to add and creates the
YAML file by hand (with provenance), so curation stays human. Non-GitHub forges
(e.g. GitLab entries in `swiss/index`) are reported as skipped.

## Link-rot detection (check)

Curated org URLs go stale when an organization is renamed or deleted on GitHub.
`check` requests each `github.com/<login>` page (tokenless, redirects
**unfollowed**) and reads only the status and any `Location` header:

```sh
python -m codeswissgov check        # no token needed (public pages)
```

- `200` → **alive**.
- `301`/`302` to a *different* login → **renamed** (the report shows the new
  URL). A redirect to the *same* login — GitHub normalizing case or a trailing
  slash — is treated as alive, not a false rename.
- `404` → **gone**.
- a transport failure → **could not be checked** (one flaky URL never aborts the
  run).

Like `ingest`, the report is **read-only guidance**: it names the renamed/gone
orgs and the action to take, but never edits `data/orgs` — a maintainer makes
the change by hand. Classification and rendering are pure
(`check/linkrot.py`); the single HTTP call is isolated in `check/__init__.py`
(`fetch_status`), so tests run offline.

## Reports (report)

`report` answers the OSPO questions from the data already on disk — no network,
no token:

```sh
python -m codeswissgov report
```

It renders four read-only sections:

- **Authority coverage** — federal org count and which cantons have a known
  GitHub org vs. publish nothing. Always printed with the **GitHub-only
  caveat**: absence means "no GitHub org found", not "publishes no open source".
- **License coverage** — share of harvested repos carrying a license; repos with
  no license are counted as compliance flags.
- **Staleness** — archived, stale (no push in ~2 years, `STALE_AFTER_DAYS`), and
  never-active repos (overlapping lenses).
- **EMBAG visibility (federal)** — the license/visibility slice over federal
  orgs only, since EMBAG ("public money → public code") binds federal bodies.

The repo-level sections need a populated `inventory.json`; until `harvest` has
run they degrade to a "run harvest" note while authority coverage still works
from `data/orgs`. The report functions are pure (`render/reports.py`); file I/O
is in `build.run_report`.

## Testing & linting

```sh
ruff check . && ruff format --check .                       # lint + format check
ruff format .                                               # apply formatting
pytest                                                      # run tests
pytest --cov=codeswissgov --cov-report=term-missing         # with coverage
```

Tests run **offline**: harvest and ingest network clients are tested against
recorded fixtures (`pytest-httpx`) under `tests/fixtures/`, never the live API.
`ruff` governs lint and format (line length 88).

## CI & automation

- **`ci.yml`** (PR/push): runs `ruff`, `pytest`, and `python -m codeswissgov
  validate`, failing on a lint error, a test failure, **or** any drift between
  `data/orgs/` and the generated views.
- **`harvest.yml`** (scheduled, Mondays 04:00 UTC + manual dispatch): runs
  `harvest`, rebuilds the views, and opens an auto-PR with the refreshed
  `inventory.json` for a human to merge. Requires a `HARVEST_GITHUB_TOKEN`
  repository secret (read-only fine-grained PAT).

## Scope & non-goals

- **GitHub only.** GitLab (incl. self-hosted / openCoDE), Bitbucket and other
  forges are out of scope. Coverage means "present on GitHub", **not**
  "publishes open source" — so absence is not evidence that an authority
  publishes nothing.
- **Federal + cantonal only.** Municipal authorities (~2,000 communes) are out
  of scope as a coverage goal.

Both are deliberate trade-offs; expanding either is an "ask first" scope change
(see `SPEC.md`).
