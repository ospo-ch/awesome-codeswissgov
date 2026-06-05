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

"""Unit + golden tests for the inventory.json renderer."""

import json

from codeswissgov.models import Organization, Repository
from codeswissgov.render.inventory import (
    SCHEMA_VERSION,
    OrgHarvest,
    load_harvest,
    render_inventory,
)


def _org(name, authority, handle):
    return Organization(
        name=name, authority=authority, url=f"https://github.com/{handle}"
    )


def test_inventory_shape_and_fields():
    text = render_inventory([_org("Swiss Admin", "federal", "admin-ch")])
    data = json.loads(text)
    assert data["schema_version"] == SCHEMA_VERSION
    assert data["organizations"] == [
        {
            "name": "Swiss Admin",
            "authority": "federal",
            "url": "https://github.com/admin-ch",
            "official": False,
            "provenance": None,
            "harvested_at": None,
            "repositories": [],
        }
    ]


def test_inventory_merges_harvested_repos():
    org = _org("Swiss Admin", "federal", "admin-ch")
    repo = Repository(
        name="tool", url="https://github.com/admin-ch/tool", license="MIT"
    )
    harvest = {
        org.url: OrgHarvest(harvested_at="2026-06-05T00:00:00Z", repositories=[repo])
    }
    entry = json.loads(render_inventory([org], harvest))["organizations"][0]
    assert entry["harvested_at"] == "2026-06-05T00:00:00Z"
    assert entry["repositories"] == [
        {
            "name": "tool",
            "url": "https://github.com/admin-ch/tool",
            "license": "MIT",
            "language": None,
            "topics": [],
            "archived": False,
            "last_activity": None,
            "has_publiccode_yml": False,
            "has_security_md": False,
        }
    ]


def test_load_harvest_round_trips_repo_data():
    org = _org("Swiss Admin", "federal", "admin-ch")
    repo = Repository(name="tool", url="https://github.com/admin-ch/tool")
    harvest = {
        org.url: OrgHarvest(harvested_at="2026-06-05T00:00:00Z", repositories=[repo])
    }
    text = render_inventory([org], harvest)
    reloaded = load_harvest(text)
    assert reloaded == harvest


def test_load_harvest_ignores_org_level_fields_and_blank():
    assert load_harvest("") == {}
    assert load_harvest("   ") == {}
    # Org-level fields present but no repos -> empty OrgHarvest, not dropped.
    text = render_inventory([_org("Swiss Admin", "federal", "admin-ch")])
    assert load_harvest(text) == {
        "https://github.com/admin-ch": OrgHarvest(harvested_at=None, repositories=[])
    }


def test_inventory_has_trailing_newline_and_preserves_unicode():
    text = render_inventory([_org("Zürich Statistics", "canton:ZH", "stat")])
    assert text.endswith("}\n")
    assert "Zürich" in text  # non-ASCII kept verbatim, not escaped


def test_inventory_is_deterministically_ordered():
    a = _org("apple", "federal", "a")
    z = _org("zebra", "federal", "z")
    assert render_inventory([z, a]) == render_inventory([a, z])


def test_committed_inventory_matches_render(repo_root, organizations):
    rendered = render_inventory(organizations)
    on_disk = (repo_root / "inventory.json").read_text(encoding="utf-8")
    assert rendered == on_disk, (
        "inventory.json is out of sync with data/orgs — run "
        "`python -m codeswissgov build`."
    )
