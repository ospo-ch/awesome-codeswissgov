# Awesome CodeSwissGov

A list of public source codes from swiss authorities.

## Swiss Federal Services

<!-- BEGIN FEDERAL LIST -->

|Service|Link|
|-------|----|
Armasuisse S+T|[Link](https://github.com/armasuissewt)
CDC-SI|[Link](https://github.com/cdc-si/)
Coordination Agency for the Preservation of Electronic Files|[Link](https://github.com/KOST-CECO)
Data Science Competence Center|[Link](https://github.com/dscc-admin-ch)
Federal Archives|[Link](https://github.com/SwissFederalArchives)
Federal Chancellery|[Link](https://github.com/swiss)
Federal Food Safety and Veterinary Office|[Link](https://github.com/BLV-OSAV-USAV)
Federal Institute of Metrology|[Link](https://github.com/metas-ch)
Federal Office for the Environment|[Link](https://github.com/foen-admin-ch)
Federal Office of Energy|[Link](https://github.com/SFOE)
Federal Office of Information Technology, Systems and Telecommunication|[Link](https://github.com/estv-admin)
Federal Office of Statistics|[Link](https://github.com/BFS-SHS-MSAS)
Federal Office of Topography|[Link](https://github.com/swisstopo)
Federal Statistical Office - Prices|[Link](https://github.com/FSO-PRICES)
i14y Interoperability Platform|[Link](https://github.com/I14Y-ch)
MeteoSwiss|[Link](https://github.com/MeteoSwiss)
Open Data Portal|[Link](https://github.com/opendata-swiss)
Open Government Data|[Link](https://github.com/ogdch)
Public Employment Service|[Link](https://github.com/alv-ch)
Swiss Admin|[Link](https://github.com/admin-ch)
Swiss Armed Forces|[Link](https://github.com/Swiss-Armed-Forces)
Swiss E-ID Ecosystem|[Link](https://github.com/e-id-admin)
Swiss Geoportal|[Link](https://github.com/geoadmin)
Swiss National Library|[Link](https://github.com/SwissNationalLibrary)
Territorial Data Lab|[Link](https://github.com/swiss-territorial-data-lab)

<!-- END FEDERAL LIST -->

## Cantonal Services (Alphabetical Order)

<!-- BEGIN CANTONAL LIST -->

|Canton|Link|
|------|----|
Aargau|[GitHub Org](https://github.com/kanton-aargau)
Appenzell Ausserrhoden|— none known yet
Appenzell Innerrhoden|[GitHub Org](https://github.com/KTAI-GIS)
Basel-Land|[Open Data](https://github.com/ogd-bl)
Basel-Stadt|[Open Data](https://github.com/opendatabs)
Bern|[GitHub Org](https://github.com/kanton-bern)
Fribourg|— none known yet
Geneva|[GitHub Org](https://github.com/republique-et-canton-de-geneve)
Glarus|— none known yet
Graubünden|— none known yet
Jura|— none known yet
Lucerne|— none known yet
Neuchâtel|[GitHub Org](https://github.com/sitn)
Nidwalden|— none known yet
Obwalden|— none known yet
Schaffhausen|— none known yet
Schwyz|— none known yet
Solothurn|[Geoinformation](https://github.com/sogis)
St. Gallen|[Office of Statistics](https://github.com/statistikSG)
Thurgau|[Open Data](https://github.com/ogdtg)
Ticino|— none known yet
Uri|— none known yet
Valais|— none known yet
Vaud|[IT Office](https://github.com/dsi-vd)
Zug|— none known yet
Zürich|[AI + Machine Learning](https://github.com/machinelearningZH)
Zürich|[Geoinformation](https://github.com/gisktzh)
Zürich|[Nature Conservation](https://github.com/FNSKtZH)
Zürich|[Office of Statistics II](https://github.com/statistikZH)
Zürich|[Open Data](https://github.com/opendatazurich)
Zürich|[Open Data - Specialist Unit](https://github.com/openZH)
Zürich|[Statistics I](https://github.com/statistikstadtzuerich)
Zürich|[Transport](https://github.com/VerkehrsbetriebeZuerich)

<!-- END CANTONAL LIST -->

## Contributing

`data/orgs/*.yaml` is the **source of truth** — one file per organization. The
tables above and `inventory.json` are **generated views**; never edit them or
the rows by hand (a build will overwrite your changes).

To add or update an organization:

1. Add or edit a file under `data/orgs/`, e.g. `data/orgs/<github-handle>.yaml`:
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

`official: true` is only permitted with a non-empty `provenance` (a registry
listing, a GitHub verified-domain match, or explicit confirmation); otherwise
the entry is an unverified candidate.

Development tooling: `pip install -r requirements-dev.txt` then `ruff check .`
and `pytest`. CI runs lint, tests, and `python -m codeswissgov validate`, which
fails if `data/orgs/` is invalid or the generated views are out of date.

### Repository-level data (harvest)

`inventory.json` also carries **harvested** repo-level data per organization
(license, language, topics, last activity, archived state, and `publiccode.yml`
/ `SECURITY.md` presence). This is produced from the GitHub API — you do not
edit it by hand:

```sh
python -m codeswissgov harvest --token "$GITHUB_TOKEN"   # read-only PAT
```

`harvest` is the only writer of repo-level data; `build` preserves it when it
regenerates the views. A scheduled workflow refreshes it weekly and opens a PR.
Coverage is **GitHub only** — authorities that publish solely off GitHub do not
appear, so absence is not evidence that an authority publishes nothing.

### Ecosystem interop (ingest)

The federal org list is meant to track the upstream
[`swiss/index`](https://github.com/swiss/index) registry. `ingest` reconciles
that registry (and any future sibling registries) against `data/orgs` and
prints a **read-only** report — it never edits `data/orgs`:

```sh
python -m codeswissgov ingest        # no token needed (public registry)
```

The report lists orgs present in a registry but **missing** from `data/orgs`
(the coverage gap to review), with a federal/cantonal hint from the registry's
section. It is guidance only: a maintainer decides what to add and creates the
`data/orgs/*.yaml` file by hand (with provenance), so curation stays human.
Non-GitHub forges (e.g. GitLab entries in `swiss/index`) are reported as
skipped — coverage is **GitHub only**.

## License 

This repository assets, content and data folders are licensed under a [CC-BY license](./LICENSE). 

All other code in this repository is licensed under the [Apache 2.0 license](./LICENSE-CODE).