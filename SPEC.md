# Spec: Swiss public-sector OSS inventory (`awesome-codeswissgov`)

**Status:** Approved — Phase 1 (Specify) complete; decisions resolved. Moving to
Phase 2 (Plan), Epic 0 first.
**Companion:** `DESIGN.md` (strategy & rationale). This spec is the buildable
contract; DESIGN is the "why".
**Scope chosen:** Full harvester vision, delivered as sequenced epics.

---

## Objective

Evolve the project from a hand-curated awesome-list into the **canonical,
machine-readable inventory of Swiss public-sector open source**: who publishes,
what they publish, under which license, and how healthy it is.

**Architecture decision (assumed by this scope):** `data/` becomes the **source
of truth**; `README.md` and `inventory.json` are **generated views**. This
dissolves the manual two-way sync that causes today's drift/orphan bugs.

**Primary users**
- OSPO operators (coverage, license, staleness, EMBAG-visibility reporting).
- Developers/citizens discovering Swiss gov open source.
- Other registries (EU/Joinup, code.gouv.fr, Developers Italia) consuming our data.

**What success looks like** — the system can answer, automatically and on a
schedule: *which authorities publish anything; which repos lack a license or are
stale; the language/license mix; where gov code reuses gov code.*

**Non-goals (accepted limitations)**
- **GitHub only.** GitLab (incl. self-hosted and openCoDE), Bitbucket, and other
  forges are **out of scope**. Authorities that publish *only* off GitHub will
  not appear, so coverage is "present on GitHub" — not "publishes open source".
  This trade-off is deliberate (GitHub is the highest-yield single source) and
  must be stated explicitly wherever coverage is reported, so the under-count is
  not mistaken for "publishes nothing". Re-introducing other platforms is an
  "ask first" scope change, not planned work.
- **Federal + cantonal only.** Municipal authorities (~2,000 communes) are **out
  of scope** as a coverage goal — exhaustive municipal crawling is mostly noise.
  Municipal entries may be accepted by submission/allowlist later, but are not
  pursued now. Adding municipal as a goal is an "ask first" scope change.

---

## Tech Stack

- **Language:** Python 3.11+ (existing).
- **Runtime deps:** `PyYAML` (existing); `httpx` (HTTP for the GitHub API);
  `pydantic` v2 (typed models + validation). *Any further runtime dep is
  "ask first".*
- **Dev deps (`requirements-dev.txt`):** `pytest`, `pytest-httpx` (mock API),
  `ruff` (lint + format).
- **CI:** GitHub Actions (lint + test + sync gate on PR; scheduled harvest).
- **Metadata standard:** align the data model with **`publiccode.yml`**
  (Foundation for Public Code) and interoperate with **`code.json`** (code.gov).

---

## Commands

```
Install:   pip install -r requirements.txt -r requirements-dev.txt
Lint:      ruff check . && ruff format --check .
Format:    ruff format .
Test:      pytest
Coverage:  pytest --cov=codeswissgov --cov-report=term-missing

# Application CLI (python -m codeswissgov <command>)
Build:     python -m codeswissgov build        # regenerate README.md + inventory.json from data/
Validate:  python -m codeswissgov validate     # schema-check data/ AND assert build is up to date
Harvest:   python -m codeswissgov harvest --token $GITHUB_TOKEN   # enrich data/ from the GitHub API
Discover:  python -m codeswissgov discover --token $GITHUB_TOKEN  # propose new orgs/repos (writes suggestions, never auto-adds)
```

---

## Project Structure

Target layout after the flip (migrated incrementally — see Epic 1):

```
src/codeswissgov/
  __init__.py
  __main__.py          → CLI dispatch (build | validate | harvest | discover)
  models.py            → pydantic models: Authority, Organization, Repository
  parse.py             → legacy README-table parser (Epic 0; removed after flip)
  harvest/
    github.py          → GitHub REST/GraphQL client (org → repos + metadata)
  discover.py          → discovery vectors (Epic 5)
  render/
    readme.py          → data/ → README.md tables (between markers)
    inventory.py       → data/ → inventory.json
    reports.py         → coverage / license / staleness reports
data/                  → SOURCE OF TRUTH (curated, git-tracked, small)
  orgs/*.yaml          → one file per organization (curation + provenance)
                         repo-level harvested data is NOT committed per-file;
                         it lives in the generated inventory.json (decision #7)
tests/                 → pytest unit + fixture-based tests
  fixtures/            → recorded API responses
.github/workflows/
  ci.yml               → lint + test + validate (sync gate) on PR/push
  harvest.yml          → scheduled (cron) harvest + auto-PR
README.md              → GENERATED VIEW (do not hand-edit data rows)
inventory.json         → GENERATED data product
SPEC.md  DESIGN.md
requirements.txt  requirements-dev.txt
```

---

## Code Style

- Keep the existing **Apache 2.0 header** on every source file.
- **Type hints everywhere**; Google-style docstrings on public functions.
- **pydantic models** for all records — no free-form dicts crossing module
  boundaries. Validation lives in the model, not the caller.
- **`ruff`** governs lint + format (line length 88, default rules). No manual
  style debates.
- Pure functions for parsing/rendering; I/O (HTTP, files) isolated at the edges
  so the core is unit-testable without the network.

```python
# Copyright 2024 ospo.ch authors
# Licensed under the Apache License, Version 2.0 (the "License"); ...

from pydantic import BaseModel, Field, HttpUrl


class Repository(BaseModel):
    """A single source repository belonging to a Swiss authority."""

    name: str
    url: HttpUrl
    authority: str = Field(description="e.g. 'federal', 'canton:ZH'")
    license: str | None = Field(default=None, description="SPDX id; None = no license = compliance flag")
    language: str | None = None
    topics: list[str] = Field(default_factory=list)
    archived: bool = False
    last_activity: str | None = None          # ISO-8601 date
    has_publiccode_yml: bool = False

    @property
    def is_compliance_flag(self) -> bool:
        """True when the repo lacks a declared license."""
        return self.license is None
```

---

## Testing Strategy

- **Framework:** `pytest`; tests in `tests/`, mirroring `src/` layout.
- **Levels:**
  - *Unit* — parsers, filename conversion, renderers, model validation. Must run
    offline; no network.
  - *Integration* — harvest clients tested against **recorded fixtures**
    (`pytest-httpx`); never hit the live API in CI.
  - *Golden* — `build` output (README tables + `inventory.json`) compared to
    committed snapshots.
- **Coverage:** ≥ 90% on `parse.py`, `models.py`, and `render/`.
- **Regression seeds (must-have cases):** markdown link / no-link / accented
  names (`Zürich`, `Graubünden`); missing table marker → clear error;
  self-cleaning removes orphans; round-trip `data/ → README → parse` is stable.

---

## Boundaries

**Always**
- Run `ruff` + `pytest` before every commit.
- Regenerate views from `data/` via `build`; never hand-edit generated rows.
- Keep generators **idempotent and self-cleaning** (no orphan files).
- Use **SPDX** license identifiers; pin dependency versions.
- Cache API responses; design harvest for **incremental** updates.

**Ask first**
- Adding any runtime dependency or changing the data **schema/model**.
- Changing CI workflows or the scheduled-harvest cadence.
- Expanding **scope** to municipal authorities or non-GitHub platforms.
- Bulk deletion of `data/` records; any destructive migration.
- Restoring i18n / multilingual rendering.

**Never**
- Commit secrets or API tokens (use GitHub Actions secrets / env).
- Surface private-repo data, or anything that amplifies a secret/PII leak.
- Mark an organization **"official"** without recorded provenance.
- Fabricate org/repo data — harvested fields come only from real API responses.
- Remove failing tests to go green without explicit approval.

---

## Epics & Success Criteria

Each epic is independently shippable and separately reviewable. Acceptance
criteria are testable.

### Epic 0 — Stabilize (README stays source; no flip yet) ✅ DONE
Fold in the audit backlog so the tool is solid before the refactor.
- [x] Generator is self-cleaning — the 3 committed orphans
      (`admin_swiss_federal_office_of_energy/_chancellery/_archives.yaml`) are
      gone and cannot recur.
- [x] `Graubüden` → `Graubünden` fixed; data regenerated.
- [x] Regex escape sequences use raw strings (no `DeprecationWarning`).
- [x] 14 no-org cantons render as plain text `— none known yet`, not `[GitHub Org]`.
- [x] Parser hardened: regex links, stripped fields, path-independent
      (`__file__`-relative), clear error on missing marker.
- [x] `ruff` + `pytest` wired; CI fails on lint error, test failure, **or**
      README↔`data/` drift (the sync gate in `.github/workflows/ci.yml`).
- [x] README has a "Contributing" section; unit tests cover the regression seeds.

### Epic 1 — Architecture flip (+ schema shape)
- [ ] `data/orgs/*.yaml` is source of truth; `python -m codeswissgov build`
      regenerates `README.md` tables and `inventory.json` deterministically.
- [ ] Existing entries migrated with no semantic loss (golden snapshot of README
      is byte-stable across a build).
- [ ] Org model shape is **`publiccode.yml`-compatible from the start**
      (decision #6 — migrate the shape once, here, not twice).
- [ ] CI `validate` gate now asserts `build` is up to date (not the old direction).

### Epic 2 — Enrichment harvester (headline feature)
- [ ] `harvest` expands each org into repos with license, language, topics,
      activity, archived, `publiccode.yml`/`SECURITY.md` presence — written to
      the generated **`inventory.json`**, not per-repo YAML (decision #7).
- [ ] GraphQL, incremental + cached; read-only PAT lifts the rate limit
      (decision #4).
- [ ] Scheduled workflow opens an auto-PR with refreshed `inventory.json`
      (human merges).

### Epic 3 — Ecosystem interop
- [ ] Ingest `swiss/index` programmatically as the **federal source**, plus ≥1
      sibling registry to seed coverage (decision #1: superset + enrichment).
- [ ] `inventory.json` documented & versioned; emit/consume `publiccode.yml`
      for EU-ecosystem interop.

### Epic 4 — Data integrity
- [ ] Link-rot detection flags 404 / renamed / deleted orgs.
- [ ] Archived/transferred repos detected and reflected in the inventory.

### Epic 5 — Discovery & reporting
- [ ] Discovery vectors (org expansion, heuristic search, domain `code.json`
      probe) produce *suggestions* (never auto-adds).
- [ ] Reports: license coverage %, stale/archived counts, **authority coverage**
      ("who publishes nothing"), and an **EMBAG-visibility** view.

### Epic 6 — Governance & community
- [ ] Verified-official provenance/badge; suggestion issue templates;
      contribution governance documented.

---

## Decisions (resolved)

1. **Positioning vs. `swiss/index` → superset + enrichment.** Ingest
   `swiss/index` programmatically as the federal source (don't hand-maintain
   what upstream already owns); add cantonal breadth + harvested metadata. Not a
   mirror. (Epic 3.)
2. **Scope → federal + cantonal only.** Municipal is out of scope as a goal
   (see Non-goals); accept by submission/allowlist later if ever.
3. **i18n → English/structured inventory.** Structural fields in English;
   original-language names/descriptions preserved verbatim. Any multilingual
   citizen view would be a *generated view* off the same `data/`, never a fork
   of the source. No translation maintenance.
4. **GitHub auth → read-only fine-grained PAT** stored as a GitHub Actions
   secret for the scheduled harvest; GraphQL to minimize calls. No GitHub App at
   this scale. (Epic 2.)
5. **"Official" verification → two-tier provenance with recorded evidence.**
   `official: true` only with a stored `provenance` source: registry listing,
   GitHub **verified-domain** match to `*.admin.ch`/`*.<canton>.ch`, or explicit
   confirmation. Otherwise `official: false` (candidate). (Epic 6; field lands
   in Epic 1 model.)
6. **Schema timing → `publiccode.yml`-compatible model shape in Epic 1.**
   Migrate the data shape once during the flip; defer full ecosystem
   import/export to Epic 3.
7. **Repo data volume → org-level YAML committed; repo data in `inventory.json`
   only.** No per-repo YAML files. `data/orgs/*.yaml` is the small curated
   source; `inventory.json` is the generated, diffable harvest artifact.
8. **Epic 1 README ordering → deterministic re-sort (no order metadata).**
   `build` sorts the federal table by service name and the cantonal table by
   (canton, unit). Migration accepts a one-time, human-reviewed README reorder
   (the 3 out-of-order federal late-adds + Zürich's sub-orgs) rather than
   maintaining a hidden `order` field/manifest. Byte-stability means
   *deterministic across builds*, not identical to the pre-flip README.
9. **Epic 1 `Organization` shape → `{name, authority, url, official,
   provenance}`.** publiccode-compatible curated fields only. The cantonal
   table's first column is derived from the `authority` code (`canton:ZH` →
   `Zürich`) via a 26-entry reference map; the federal link label is the
   constant `Link`. Harvested fields (license/language/topics/activity/…) are
   **not** in the org YAML — they land in `inventory.json` in Epic 2. In Epic 1,
   `inventory.json` is **org-level only**.

---

## Review checklist (Phase 1 gate)

- [x] Covers the six core areas (objective, stack, commands, structure, style, testing).
- [x] Boundaries defined (Always / Ask first / Never).
- [x] Success criteria are specific and testable (per epic).
- [x] Saved to the repository (`SPEC.md`).
- [x] Open questions resolved (see Decisions).
- [x] **Human reviewed and approved.** Cleared to advance to Phase 2 (Plan),
      starting with the unblocked Epic 0.
