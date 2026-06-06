# Contributing & governance

Thanks for helping build the inventory of Swiss public-sector open source. This
page covers **what** the project accepts and **how** it is governed. For the
**mechanics** — installing, running the CLI, the data model, harvesting, and
testing — see [DEVELOPMENT.md](./DEVELOPMENT.md).

## Ways to contribute

- **Suggest an organization** (no GitHub know-how needed). Open a
  [suggestion issue](../../issues/new/choose) and fill in the form. A maintainer
  reviews it and curates the data by hand.
- **Add or edit data directly.** Add a file under `data/orgs/` and regenerate
  the views — the step-by-step is in
  [DEVELOPMENT.md](./DEVELOPMENT.md#contributing).

## Scope

Two deliberate boundaries keep the list meaningful (full rationale in
[SPEC.md](./SPEC.md)):

- **GitHub only.** GitLab (incl. self-hosted / openCoDE), Bitbucket, and other
  forges are out of scope. Coverage means "present on GitHub", **not**
  "publishes open source" — so absence is never evidence that an authority
  publishes nothing.
- **Federal + cantonal only.** Municipal authorities (~2,000 communes) are out
  of scope as a coverage goal.

Expanding either boundary is an "ask first" change, not routine work.

## What "official" means (provenance policy)

Every organization carries an `official` flag. It is set to `true` **only** with
recorded `provenance` — evidence stored alongside the entry. Accepted evidence
(SPEC decision #5):

- a listing in a recognized registry (e.g. `github.com/swiss/index`);
- a GitHub **verified-domain** match to an `*.admin.ch` / `*.<canton>.ch`
  domain; or
- an explicit confirmation from the authority.

Without such evidence the entry stays `official: false` — an unverified
candidate. Verified-official orgs are marked with a ✅ in the README tables.
We never mark an organization official without recorded provenance.

## How curation works

The automated tools are **read-only**: they surface gaps and problems, but a
human always decides what changes:

- `ingest` reconciles sibling registries (`swiss/index`) against `data/orgs/`
  and reports orgs that are listed upstream but missing locally.
- `check` flags link rot — renamed or deleted org URLs.
- `report` summarizes license coverage, staleness, authority coverage, and
  EMBAG visibility.

None of them edit `data/orgs/`. Maintainers apply the fixes by hand (with
provenance), so curation stays human and auditable.

## Pull request expectations

- `ruff check . && ruff format --check .`, `pytest`, and
  `python -m codeswissgov validate` must all pass (CI enforces them).
- Regenerate the views (`python -m codeswissgov build`) and commit the updated
  `README.md` / `inventory.json` alongside any `data/orgs/` change — never edit
  the generated rows by hand.

## Code of conduct

Be respectful and constructive. This is a public-sector transparency project;
keep discussion focused on the data and the tooling.
