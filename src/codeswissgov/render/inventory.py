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

"""Render ``data/orgs`` into the ``inventory.json`` data product.

Epic 1 ships an **org-level** inventory (no repo-level data — that arrives in
Epic 2, SPEC decision #7). Output is deterministic: canonical render order,
two-space indent, trailing newline, non-ASCII preserved.
"""

import json

from ..models import Organization
from . import render_order

SCHEMA_VERSION = "1.0"


def render_inventory(orgs: list[Organization]) -> str:
    """Return the ``inventory.json`` text for ``orgs``."""
    payload = {
        "schema_version": SCHEMA_VERSION,
        "organizations": [o.model_dump() for o in render_order(orgs)],
    }
    return json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
