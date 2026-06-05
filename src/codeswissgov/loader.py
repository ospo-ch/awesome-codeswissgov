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

"""Load the curated source of truth (``data/orgs/*.yaml``) into models."""

from pathlib import Path

import yaml
from pydantic import ValidationError

from .models import Organization


def load_organizations(orgs_dir: Path) -> list[Organization]:
    """Load and validate every ``*.yaml`` under ``orgs_dir``.

    Files are read in filename order for determinism; renderers re-sort as
    needed. Raises ``ValueError`` (naming the offending file) on a schema
    violation so ``validate`` can report it clearly.
    """
    orgs: list[Organization] = []
    for path in sorted(orgs_dir.glob("*.yaml")):
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
        try:
            orgs.append(Organization(**raw))
        except ValidationError as exc:
            raise ValueError(f"{path.name}: invalid organization\n{exc}") from exc
    return orgs
