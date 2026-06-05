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

"""Regenerate the generated views (README.md, inventory.json) from data/orgs.

Shared by the ``build`` and ``validate`` CLI commands (T5).
"""

from dataclasses import dataclass
from pathlib import Path

from .loader import load_organizations
from .render.inventory import render_inventory
from .render.readme import render_readme

# Repo root: src/codeswissgov/build.py -> parents[2].
DEFAULT_ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class RenderResult:
    """The rendered README and inventory text plus their target paths."""

    readme_path: Path
    readme_text: str
    inventory_path: Path
    inventory_text: str


def render_all(root: Path = DEFAULT_ROOT) -> RenderResult:
    """Render both views in memory (no writes). Used by build and validate."""
    readme_path = root / "README.md"
    inventory_path = root / "inventory.json"
    orgs = load_organizations(root / "data" / "orgs")
    return RenderResult(
        readme_path=readme_path,
        readme_text=render_readme(orgs, readme_path.read_text(encoding="utf-8")),
        inventory_path=inventory_path,
        inventory_text=render_inventory(orgs),
    )


def build(root: Path = DEFAULT_ROOT) -> RenderResult:
    """Render and write README.md and inventory.json. Returns what was written."""
    result = render_all(root)
    result.readme_path.write_text(result.readme_text, encoding="utf-8")
    result.inventory_path.write_text(result.inventory_text, encoding="utf-8")
    return result


def validate(root: Path = DEFAULT_ROOT) -> list[str]:
    """Return the names of generated files that are out of date (empty = in sync).

    Schema-checks ``data/orgs`` as a side effect of rendering; a violation
    propagates as ``ValueError`` (naming the offending file).
    """
    result = render_all(root)
    stale: list[str] = []
    if result.readme_text != result.readme_path.read_text(encoding="utf-8"):
        stale.append(result.readme_path.name)
    if result.inventory_text != result.inventory_path.read_text(encoding="utf-8"):
        stale.append(result.inventory_path.name)
    return stale
