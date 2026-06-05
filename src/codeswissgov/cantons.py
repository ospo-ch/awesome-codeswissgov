# Copyright 2024 ospo.ch authors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Swiss canton reference data.

The cantonal table's first column is derived from an organization's
``authority`` code (``canton:ZH`` -> ``Zürich``) via this map (SPEC decision
#9). Display names are the English/original forms used in ``README.md`` and must
match it verbatim so that ``build`` round-trips byte-for-byte.
"""

# Maps the ISO 3166-2:CH canton code to the display name used in README.md.
CANTONS: dict[str, str] = {
    "AG": "Aargau",
    "AI": "Appenzell Innerrhoden",
    "AR": "Appenzell Ausserrhoden",
    "BE": "Bern",
    "BL": "Basel-Land",
    "BS": "Basel-Stadt",
    "FR": "Fribourg",
    "GE": "Geneva",
    "GL": "Glarus",
    "GR": "Graubünden",
    "JU": "Jura",
    "LU": "Lucerne",
    "NE": "Neuchâtel",
    "NW": "Nidwalden",
    "OW": "Obwalden",
    "SG": "St. Gallen",
    "SH": "Schaffhausen",
    "SO": "Solothurn",
    "SZ": "Schwyz",
    "TG": "Thurgau",
    "TI": "Ticino",
    "UR": "Uri",
    "VD": "Vaud",
    "VS": "Valais",
    "ZG": "Zug",
    "ZH": "Zürich",
}

# Valid canton codes, for authority validation.
CANTON_CODES: frozenset[str] = frozenset(CANTONS)

# Reverse lookup (display name -> code), used by the one-shot README migration.
CODE_BY_DISPLAY: dict[str, str] = {name: code for code, name in CANTONS.items()}


def canton_display(code: str) -> str:
    """Return the README display name for a canton ``code`` (e.g. ``ZH``)."""
    return CANTONS[code]
