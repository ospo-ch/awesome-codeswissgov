# Design Proposal: From an awesome-list to a Swiss public-sector OSS inventory

**Status:** Draft for discussion
**Scope:** Evolves `awesome-codeswissgov` from a hand-curated link list into the
canonical, machine-readable inventory of Swiss public-sector open source.
**Supersedes:** `issues.md` (its content is folded into Phase 0 and the appendix).

---

## 1. Context & motivation

`awesome-codeswissgov` is currently an *awesome-list*: `README.md` holds two
hand-maintained markdown tables (federal + cantonal GitHub orgs), and
`scripts/create_yamls.py` derives one `data/*.yaml` file per row for machine
consumption. It is curated under the `ospo-ch` org and synced from the federal
`github.com/swiss/index`.

What makes this strategically important is its legal backdrop. Switzerland's
**EMBAG** law (in force since 2024) makes *"public money → public code"* the
**default** for federal authorities: software developed by or for them is
expected to be released openly unless there's a specific reason not to. That
turns a nice-to-have directory into the visible edge of a **discovery,
inventory, and compliance** problem that an OSPO must run continuously.

**Today we track ~50 orgs. An OSPO needs to know the repositories inside them —
their licenses, activity, and health — and which authorities publish nothing at
all.** That is the gap this proposal closes.

---

## 2. North star

> The canonical, machine-readable inventory of Swiss public-sector open source:
> **who** publishes, **what** they publish, under **which license**, and **how
> healthy** it is — consumable as data, with the README as one rendered view.

Success looks like being able to answer, automatically and on a schedule:

- Which authorities (federal / cantonal) publish *anything*?
- Which repositories have **no license** or are **archived/stale**?
- What is the language / license / activity mix across the public sector?
- Where does Swiss gov code **reuse** other Swiss gov code?

---

## 3. Proposed architecture

Flip the data flow from **"human edits README → script derives YAML"** to
**"harvester produces data → README is a generated view."**

```
            ┌─────────────────────────┐
 sources ──▶│  Discovery + Harvester  │──▶  data/ (structured inventory)
 (orgs,     │  (GitHub API,            │          │
  registries│   publiccode.yml, code.json)        ├──▶ README.md  (generated view)
  domains)  └─────────────────────────┘          ├──▶ inventory.json (data product / API)
                                                  └──▶ reports (license %, stale, coverage)
```

Key consequences:

- **The sync/orphan class of bugs disappears.** When `data/` is the source and
  the README is regenerated, there is no manual two-way sync to drift, and a
  self-cleaning generator removes stale records by construction.
- **`data/` becomes the product**, not a byproduct. The README, a JSON feed, and
  reports are all *views* of the same dataset.
- **Curation stays human where it matters** (verifying that an org is genuinely
  official) but enrichment (license, activity, language) is automated.

### 3.1 Adopt a standard metadata schema

Replace the ad-hoc `{name, link_title, link_url}` shape with a model aligned to
**`publiccode.yml`** (Foundation for Public Code; harvested by Italy's
*Developers Italia*) and interoperable with the US **`code.json`** (code.gov).

Proposed per-record fields (org- and repo-level):

| Field | Source | Notes |
|-------|--------|-------|
| `name` | curated | display name |
| `authority` | curated | e.g. `federal`, `canton:ZH` |
| `official` | curated | verified-official flag / provenance |
| `url` | curated/harvested | GitHub org or repo URL |
| `license` | harvested | SPDX id; **empty = compliance flag** |
| `language` | harvested | primary language |
| `topics` | harvested | repo topics |
| `last_activity` | harvested | last pushed/commit date |
| `archived` | harvested | bool |
| `has_publiccode_yml` | harvested | self-description present |

Aligning with `publiccode.yml` lets us **ingest from and be ingested by** the EU
ecosystem for free, and lets us nudge agencies to drop a `publiccode.yml` in
their repos so they become self-describing.

---

## 4. Discovery strategy

Discovery is the hard, never-finished part. Vectors, roughly by yield:

1. **Org expansion** — for each known org, list members and their *other* org
   memberships; gov developers cluster.
2. **Heuristic search** on GitHub: `kanton-*`, `stadt-*`, `*-admin-ch`,
   canton names, "Amt für…", official domains in profiles.
3. **Cross-reference sibling registries** — `swiss/index`, France's
   `code.gouv.fr` (API), Germany's **openCoDE**, Developers Italia, EU
   **Joinup**, US **code.gov**. Reuse their work to surface the *GitHub* orgs
   they list.
4. **Domain harvesting** — probe `*.admin.ch` / `*.<canton>.ch` for a published
   `code.json` / `publiccode.yml` at a well-known path (the code.gov model).
5. **Package registries** — gov orgs on npm/PyPI/Maven/Docker Hub (linking back
   to GitHub source).
6. **Procurement signals** — SIMAP/tender data referencing repos.
7. **Crowdsourcing** — a one-click "suggest an org/repo" issue template.

> **Scope note:** discovery surfaces **GitHub** orgs/repos only. Sources that
> point to GitLab / openCoDE / Bitbucket are noted but not inventoried — see the
> accepted-limitation entry under Challenges.

---

## 5. Roadmap

### Phase 0 — Stabilize the current tool (the `issues.md` backlog)

Quick, self-contained fixes that also de-risk the bigger refactor. Detailed in
the [appendix](#appendix-phase-0-issue-detail).

- Make the generator **self-cleaning** (remove orphaned YAML) — **bug**
- Fix the **"Graubüden" → "Graubünden"** typo — **bug**
- Fix **invalid regex escape sequences** (raw strings) — **bug**
- Add **CI** to enforce README ↔ `data/` sync — **DX**
- Render the **14 no-org cantons** as plain text, not broken `[GitHub Org]` — **bug**
- Harden the **parser** (regex links, strip fields, path-independent, clear
  errors) — **DX**
- Add a **Contributing** section and **unit tests** — **docs / DX**

### Phase 1 — Enrichment harvester (the headline feature)

- GitHub API harvester: expand each org into repos with license, language,
  activity, archived status, `publiccode.yml`/`SECURITY.md` presence.
- Scheduled GitHub Action (cron) writes enriched `data/`.
- **Regenerate the README from `data/`** (architecture flip).

### Phase 2 — Schema & ecosystem alignment

- Migrate to the `publiccode.yml`-aligned model (§3.1).
- Publish `inventory.json` as a data product / lightweight API.
- Ingest from `swiss/index` and at least one sibling registry to seed coverage.

### Phase 3 — Discovery automation & reporting

- Implement discovery vectors §4 (org expansion, heuristic search, domain probe).
- Reports: license coverage %, stale/archived counts, **authority coverage**
  ("who publishes nothing"), and a simple **EMBAG visibility** view.

### Phase 4 — Governance & community

- Verification/provenance model for "official" orgs (badge).
- Contribution governance, suggestion templates, link-rot detection bot.

---

## 6. Challenges & risks

- **"Has a GitHub org" ≠ "EMBAG-compliant."** The list must not imply compliance
  it can't verify.
- **Official vs. unofficial / personal** projects — needs a provenance model or
  it publishes noise.
- **Coverage limitation (accepted): GitHub only.** GitLab (incl. self-hosted /
  openCoDE), Bitbucket and other forges are out of scope; authorities that
  publish only off GitHub won't appear. Coverage means "present on GitHub", not
  "publishes open source" — state this wherever numbers are reported so the
  under-count isn't read as "publishes nothing".
- **Org churn** — renames, archives, deletions → link rot. Automation must
  detect 404s.
- **Multilingual reality.** CH has 4 national languages; i18n was just dropped
  (commit `67e33e8`). An *inventory* can stay structured/English, but a
  *citizen-facing catalog* may need DE/FR/IT/RM — a conscious product decision,
  not a silent default.
- **Security/privacy footgun.** Surfacing repos can amplify accidental
  secret/PII leaks; consider basic hygiene checks rather than pure advertising.
- **Sustainability.** Manual curation doesn't scale past a few dozen orgs;
  without automation the list decays.
- **Positioning vs. `swiss/index`.** Resolved as a superset that adds cantonal
  breadth + enrichment and ingests `swiss/index` as the federal source — not a
  mirror, to avoid duplicate work and user confusion.
- **API rate limits & auth.** Harvesting at scale needs a token and caching;
  design for incremental updates.

---

## 7. Decisions (resolved — see `SPEC.md` for detail)

1. **Architecture flip** — ✅ `data/` is the source of truth; README is a
   generated view.
2. **Schema** — ✅ adopt a `publiccode.yml`-compatible model shape during the
   flip (Epic 1); defer full import/export to Epic 3.
3. **Positioning vs. `swiss/index`** — ✅ superset + enrichment; ingest
   `swiss/index` as the federal source rather than mirroring it.
4. **Scope** — ✅ federal + cantonal only; municipal out of scope (submission/
   allowlist only, if ever).
5. **i18n** — ✅ English/structured inventory; any multilingual view is generated
   off the same `data/`, not a fork.
6. **GitHub auth** — ✅ read-only fine-grained PAT in an Actions secret; GraphQL.
7. **Repo data volume** — ✅ org-level YAML committed; repo data lives only in the
   generated `inventory.json` (no per-repo files).

---

## Appendix: Phase 0 issue detail

Audit findings from the Senior Staff review. README.md is currently the source
of truth; `scripts/create_yamls.py` generates the per-entry `data/*.yaml` files.

Status legend: 🐞 bug · 🛠️ DX/maintainability · 📄 docs

### High priority

**1. 🐞 Generator leaves orphaned YAML files behind.**
`create_yamls.py` writes files but never deletes them, so renamed/removed README
entries leave stale files in `data/` forever. **3 orphans** are currently
committed (58 README entries, 61 files):
`data/admin_swiss_federal_office_of_energy.yaml`,
`data/admin_swiss_federal_chancellery.yaml`,
`data/admin_swiss_federal_archives.yaml`.
*Fix:* track files written during a run and remove any `data/*.yaml` not in that
set. (Dissolved entirely by the Phase 1 architecture flip.)

**2. 🐞 Typo in cantonal data: "Graubüden".**
`README.md:54` reads `Graubüden` — should be `Graubünden`; the typo propagates
into the filename (`graubuden_github_org.yaml`) and YAML.
*Fix:* correct the spelling and regenerate.

**3. 🐞 Invalid escape sequences in regexes.**
`create_yamls.py:87-88` use non-raw strings `"[^\w\s]"` and `"[-\s]+"`
(`DeprecationWarning` on 3.11, `SyntaxWarning` on 3.12+, future hard error).
*Fix:* raw strings (`r"[^\w\s]"`, `r"[-\s]+"`).

### Medium priority

**4. 🛠️ Nothing keeps README and `data/` in sync.**
YAML is generated manually; the two drift silently and no CI catches it.
*Fix:* GitHub Actions workflow that installs deps, runs the generator, and fails
with `git diff --exit-code data/` on drift.

**5. 🐞 Broken markdown for cantons with no org.**
14 cantons use `[GitHub Org]` with no URL (Appenzell Ausserrhoden, Fribourg,
Glarus, Graubünden, Jura, Lucerne, Nidwalden, Obwalden, Schaffhausen, Schwyz,
Ticino, Uri, Valais, Zug); with no target they render as literal `[GitHub Org]`.
*Decision (agreed):* keep them as intentional placeholders but render plain text
(e.g. `— none known yet`); the generator maps link-less cells to empty
`link_title`/`link_url` and names the file after the canton only.

**6. 🛠️ Fragile parser.**
Relies on exact marker strings (`list.index()` raises uncaught `ValueError` if a
marker moves); naive `|`/`]` splitting; `name` not stripped; must run from repo
root (hard-coded `./README.md`).
*Fix:* regex link parsing, strip fields, resolve paths from `__file__`, clear
error when a marker is missing.

### Low priority

**7. 📄 No contributor guidance.** No section explains the README → `data/`
workflow, running `python3 scripts/create_yamls.py`, or the YAML schema.
*Fix:* add a short "Contributing" section.

**8. 🛠️ No tests.** Add unit tests for `parse_row` and `convert_to_filename`
(link, no-link, accented names).

**9. 🛠️ Tooling hygiene (optional).** No linter/formatter config
(`ruff`/`black`) despite a Python-shaped `.gitignore`; consider a
dev-requirements set if tests/lint are added.
