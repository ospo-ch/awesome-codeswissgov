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
#

"""
This script generates yaml files from the README content.

README.md is the single source of truth. Each row of the federal and cantonal
tables is exported to one yaml file under data/ for machine consumption. The
script is idempotent and self-cleaning: yaml files in data/ that no longer
correspond to a README row are removed.
"""

import re
import sys
import unicodedata
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
README_PATH = REPO_ROOT / "README.md"
DATA_DIR = REPO_ROOT / "data"

# Matches a markdown link: [title](url)
LINK_RE = re.compile(r"\[([^\]]*)\]\(([^)]*)\)")


def _extract_table(lines, header, end_marker):
    """
    Return the data rows of a markdown table delimited by ``header`` (the
    ``|Col|Col|`` header line) and ``end_marker`` (an HTML comment closing the
    list). The header separator row that follows the header is skipped, and
    blank lines are dropped.
    """
    try:
        start = lines.index(header) + 2
        end = lines.index(end_marker) - 1
    except ValueError as exc:
        raise ValueError(
            f"Could not locate table markers {header!r} / {end_marker!r} in "
            f"{README_PATH}. Has the README structure changed?"
        ) from exc
    return [line for line in lines[start:end] if line.strip()]


def read_readme():
    """
    Read the README file and return the data rows of the federal services table
    and the cantonal services table.
    """
    lines = README_PATH.read_text(encoding="utf-8").splitlines(keepends=True)

    fed = _extract_table(lines, "|Service|Link|\n", "<!-- END FEDERAL LIST -->\n")
    canton = _extract_table(lines, "|Canton|Link|\n", "<!-- END CANTONAL LIST -->\n")
    return fed, canton


def parse_row(row: str):
    """
    Parse a markdown table row of the form ``name|[link_title](link_url)``.

    Cells without a markdown link (plain-text placeholders such as
    "— none known yet") yield empty ``link_title`` and ``link_url``.
    """
    cells = [cell.strip() for cell in row.strip().split("|")]
    name = cells[0]
    link_title = ""
    link_url = ""

    if len(cells) > 1:
        match = LINK_RE.search(cells[1])
        if match:
            link_title, link_url = match.group(1), match.group(2)

    return dict(
        name=name,
        link_title=link_title,
        link_url=link_url,
    )


def convert_to_filename(name: str):
    """
    Convert to ASCII, remove characters which aren't alphanumeric or underscore.
    Strip leading and trailing whitespace. Convert to lowercase. Converts spaces
    and dashes to single underscore.

    This code is based on:
    https://github.com/django/django/blob/cdcd604ef8f650533eff6bd63a517ebb4ffddf96/django/utils/text.py#L452
    """
    name = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode("ascii")
    name = re.sub(r"[^\w\s]", "", name.lower())
    name = re.sub(r"[-\s]+", "_", name).strip("_")
    return name


def write_yaml(file_name: str, data: dict):
    """Write ``data`` to ``data/<file_name>.yaml`` and return the path."""
    path = DATA_DIR / f"{file_name}.yaml"
    with path.open("w", encoding="utf-8") as file:
        yaml.dump(
            data,
            file,
            default_flow_style=False,
            allow_unicode=True,
            sort_keys=False,
        )
    return path


def create_yaml_files():
    """
    Extract data from the README file and (re)create one yaml file per entry,
    removing any stale yaml files that no longer match a README row.
    """
    fed, canton = read_readme()
    DATA_DIR.mkdir(exist_ok=True)

    written = set()

    # process federal service data
    for row in fed:
        data = parse_row(row)
        file_name = convert_to_filename("_".join(("admin", data["name"])))
        written.add(write_yaml(file_name, data))

    # process canton data
    for row in canton:
        data = parse_row(row)
        parts = [data["name"]]
        if data["link_title"]:
            parts.append(data["link_title"])
        file_name = convert_to_filename("_".join(parts))
        written.add(write_yaml(file_name, data))

    # remove stale yaml files that are no longer backed by a README row
    for existing in DATA_DIR.glob("*.yaml"):
        if existing not in written:
            existing.unlink()


if __name__ == "__main__":
    sys.exit(create_yaml_files())
