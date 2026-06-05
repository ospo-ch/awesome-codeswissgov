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

"""Generated views of the inventory (README tables, inventory.json).

Ordering is deterministic and case-insensitive (SPEC decision #8): federal by
service name, cantonal by (canton, unit name).
"""

from ..cantons import canton_display
from ..models import Organization


def federal_sorted(orgs: list[Organization]) -> list[Organization]:
    """Federal orgs ordered by service name (case-insensitive)."""
    return sorted((o for o in orgs if o.is_federal), key=lambda o: o.name.casefold())


def cantonal_sorted(orgs: list[Organization]) -> list[Organization]:
    """Cantonal orgs ordered by (canton display name, unit name)."""
    return sorted(
        (o for o in orgs if not o.is_federal),
        key=lambda o: (canton_display(o.canton_code).casefold(), o.name.casefold()),
    )


def render_order(orgs: list[Organization]) -> list[Organization]:
    """Canonical render order: federal first, then cantonal."""
    return federal_sorted(orgs) + cantonal_sorted(orgs)
