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

"""One-shot migration: README.md tables -> data/orgs/*.yaml (Epic 1, T3).

Throwaway tooling. Run once to seed the new source of truth from the legacy
README tables; deleted together with the old generator in T7. After the flip the
data flows the other way (README.md is generated from data/orgs/).

Cantons with no known org are NOT written here — they are absences, derived as
``— none known yet`` by the renderer from the canton list (SPEC decision #9).

    python scripts/migrate_to_orgs.py
"""

import re
import sys
import unicodedata
from pathlib import Path

import yaml

from codeswissgov.cantons import CODE_BY_DISPLAY
from codeswissgov.models import Organization

REPO_ROOT = Path(__file__).resolve().parent.parent
README_PATH = REPO_ROOT / "README.md"
ORGS_DIR = REPO_ROOT / "data" / "orgs"

LINK_RE = re.compile(r"\[([^\]]*)\]\(([^)]*)\)")


def _extract_table(lines: list[str], header: str, end_marker: str) -> list[str]:
    """Return the non-blank data rows of the table between ``header`` and end."""
    try:
        start = lines.index(header) + 2
        end = lines.index(end_marker) - 1
    except ValueError as exc:
        raise ValueError(
            f"Could not locate table markers {header!r} / {end_marker!r}."
        ) from exc
    return [line for line in lines[start:end] if line.strip()]


def parse_row(row: str) -> tuple[str, str, str]:
    """Parse ``col0|[label](url)`` into ``(col0, label, url)`` (empty if none)."""
    cells = [cell.strip() for cell in row.strip().split("|")]
    col0 = cells[0]
    label = url = ""
    if len(cells) > 1:
        match = LINK_RE.search(cells[1])
        if match:
            label, url = match.group(1), match.group(2)
    return col0, label, url


def slugify(value: str) -> str:
    """ASCII, lowercase, non-alphanumeric runs -> single underscore."""
    value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode()
    value = re.sub(r"[^a-z0-9]+", "_", value.lower())
    return value.strip("_")


def handle_from_url(url: str) -> str:
    """Last path segment of a GitHub org URL (e.g. ``cdc-si`` from ``.../cdc-si/``)."""
    return url.rstrip("/").rsplit("/", 1)[-1]


def main() -> int:
    lines = README_PATH.read_text(encoding="utf-8").splitlines(keepends=True)
    fed = _extract_table(lines, "|Service|Link|\n", "<!-- END FEDERAL LIST -->\n")
    canton = _extract_table(lines, "|Canton|Link|\n", "<!-- END CANTONAL LIST -->\n")

    records: list[tuple[str, Organization]] = []

    for row in fed:
        name, _label, url = parse_row(row)
        org = Organization(name=name, authority="federal", url=url)
        records.append((slugify(handle_from_url(url)), org))

    for row in canton:
        canton_name, label, url = parse_row(row)
        if not url:
            continue  # no-org canton: derived at render time, not stored
        code = CODE_BY_DISPLAY[canton_name]
        org = Organization(name=label, authority=f"canton:{code}", url=url)
        records.append((slugify(handle_from_url(url)), org))

    ORGS_DIR.mkdir(parents=True, exist_ok=True)
    written: dict[str, Organization] = {}
    for slug, org in records:
        if slug in written:
            raise SystemExit(f"slug collision: {slug!r}")
        written[slug] = org
        (ORGS_DIR / f"{slug}.yaml").write_text(
            yaml.safe_dump(
                org.model_dump(),
                default_flow_style=False,
                allow_unicode=True,
                sort_keys=False,
            ),
            encoding="utf-8",
        )

    print(f"wrote {len(written)} org files to {ORGS_DIR.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
