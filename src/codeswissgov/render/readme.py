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

"""Render ``data/orgs`` into the README federal and cantonal tables.

Only the content between the ``<!-- BEGIN/END … LIST -->`` markers is replaced;
the rest of the README (intro, Contributing, License) is left untouched.
"""

import re

from ..cantons import CANTONS, canton_display
from ..models import Organization
from . import federal_sorted

FEDERAL_HEADER = "|Service|Link|\n|-------|----|\n"
CANTONAL_HEADER = "|Canton|Link|\n|------|----|\n"
# Rendered for a canton with no known GitHub org (derived, not stored).
NONE_KNOWN = "— none known yet"

FEDERAL_BEGIN = "<!-- BEGIN FEDERAL LIST -->"
FEDERAL_END = "<!-- END FEDERAL LIST -->"
CANTONAL_BEGIN = "<!-- BEGIN CANTONAL LIST -->"
CANTONAL_END = "<!-- END CANTONAL LIST -->"


def _federal_block(orgs: list[Organization]) -> str:
    rows = "".join(f"{o.name}|[Link]({o.url})\n" for o in federal_sorted(orgs))
    return f"\n{FEDERAL_HEADER}{rows}\n"


def _cantonal_block(orgs: list[Organization]) -> str:
    rows: list[str] = []
    for code in sorted(CANTONS, key=lambda c: CANTONS[c].casefold()):
        display = canton_display(code)
        units = sorted(
            (o for o in orgs if o.canton_code == code), key=lambda o: o.name.casefold()
        )
        if not units:
            rows.append(f"{display}|{NONE_KNOWN}\n")
        else:
            rows.extend(f"{display}|[{o.name}]({o.url})\n" for o in units)
    return f"\n{CANTONAL_HEADER}{''.join(rows)}\n"


def _replace_between(text: str, begin: str, end: str, inner: str) -> str:
    pattern = re.compile(re.escape(begin) + r"\n.*?" + re.escape(end), re.DOTALL)
    if not pattern.search(text):
        raise ValueError(f"Could not find markers {begin!r} / {end!r} in README.")
    return pattern.sub(lambda _m: f"{begin}\n{inner}{end}", text)


def render_readme(orgs: list[Organization], text: str) -> str:
    """Return ``text`` with both table bodies regenerated from ``orgs``."""
    text = _replace_between(text, FEDERAL_BEGIN, FEDERAL_END, _federal_block(orgs))
    text = _replace_between(text, CANTONAL_BEGIN, CANTONAL_END, _cantonal_block(orgs))
    return text
