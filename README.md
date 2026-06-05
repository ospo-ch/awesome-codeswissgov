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

`README.md` is the **single source of truth**. The lists above are the two
markdown tables delimited by the `<!-- BEGIN/END FEDERAL LIST -->` and
`<!-- BEGIN/END CANTONAL LIST -->` comments. The per-entry files under `data/`
are **generated** from them — never edit `data/` by hand.

To add or update an organization:

1. Edit the relevant table in `README.md`. Each row is `Name|[Link text](url)`.
   For an authority with no known GitHub org, use plain text (e.g.
   `Canton|— none known yet`) instead of a link.
2. Regenerate the data files:
   ```sh
   pip install -r requirements.txt
   python scripts/create_yamls.py
   ```
   The generator is idempotent and self-cleaning (it removes `data/` files that
   no longer match a row).
3. Commit both the `README.md` and `data/` changes.

Each generated file has the schema:

```yaml
name: <display name>
link_title: <link text, empty if none>
link_url: <GitHub URL, empty if none>
```

Development tooling (optional): `pip install -r requirements-dev.txt` then
`ruff check .` and `pytest`. CI enforces lint, tests, and that `data/` stays in
sync with `README.md`.

## License 

This repository assets, content and data folders are licensed under a [CC-BY license](./LICENSE). 

All other code in this repository is licensed under the [Apache 2.0 license](./LICENSE-CODE).