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

"""Render ``data/orgs`` (+ harvested repos) into the ``inventory.json`` product.

``inventory.json`` is the **single** committed artifact that carries repo-level
data (SPEC decision #7). ``harvest`` is the sole writer of that repo data;
``build`` regenerates the org-level fields from ``data/orgs`` while *preserving*
the ``repositories``/``harvested_at`` blocks already present, so it stays offline
and deterministic. Output is canonical: render order, two-space indent, trailing
newline, non-ASCII preserved.
"""

import json
from dataclasses import dataclass, field

from ..models import Organization, Repository
from . import render_order

SCHEMA_VERSION = "2.0"


@dataclass(frozen=True)
class OrgHarvest:
    """Harvested repo-level data for one organization (keyed elsewhere by url)."""

    harvested_at: str | None = None
    repositories: list[Repository] = field(default_factory=list)


def load_harvest(inventory_text: str) -> dict[str, OrgHarvest]:
    """Parse repo-level harvest data from an existing ``inventory.json``.

    Returns a mapping of org ``url`` -> :class:`OrgHarvest`. Org-level fields are
    ignored (they are regenerated from ``data/orgs``); only ``harvested_at`` and
    ``repositories`` are carried forward, the latter validated through the model
    so corruption surfaces clearly. Empty/blank text yields an empty mapping.
    """
    if not inventory_text.strip():
        return {}
    data = json.loads(inventory_text)
    harvest: dict[str, OrgHarvest] = {}
    for entry in data.get("organizations", []):
        repos = [Repository(**r) for r in entry.get("repositories", [])]
        harvest[entry["url"]] = OrgHarvest(
            harvested_at=entry.get("harvested_at"),
            repositories=repos,
        )
    return harvest


def render_inventory(
    orgs: list[Organization],
    harvest: dict[str, OrgHarvest] | None = None,
) -> str:
    """Return the ``inventory.json`` text for ``orgs`` plus any harvested repos.

    ``harvest`` maps org ``url`` -> :class:`OrgHarvest`; orgs without an entry
    render with ``harvested_at: null`` and an empty ``repositories`` list.
    """
    harvest = harvest or {}
    payload = {
        "schema_version": SCHEMA_VERSION,
        "organizations": [
            _org_entry(o, harvest.get(o.url)) for o in render_order(orgs)
        ],
    }
    return json.dumps(payload, indent=2, ensure_ascii=False) + "\n"


def _org_entry(org: Organization, harvested: OrgHarvest | None) -> dict:
    entry = org.model_dump()
    entry["harvested_at"] = harvested.harvested_at if harvested else None
    repos = harvested.repositories if harvested else []
    entry["repositories"] = [r.model_dump() for r in repos]
    return entry
