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

"""Unit tests for scripts/create_yamls.py (the README -> data/ generator)."""

import create_yamls as cy
import pytest

MINIMAL_README = """\
# Test

## Federal

<!-- BEGIN FEDERAL LIST -->

|Service|Link|
|-------|----|
Swiss Admin|[Link](https://github.com/admin-ch)

<!-- END FEDERAL LIST -->

## Cantonal

<!-- BEGIN CANTONAL LIST -->

|Canton|Link|
|------|----|
Aargau|[GitHub Org](https://github.com/kanton-aargau)
Jura|— none known yet

<!-- END CANTONAL LIST -->
"""


# --- parse_row --------------------------------------------------------------


def test_parse_row_with_link():
    row = "Swiss Admin|[Link](https://github.com/admin-ch)\n"
    assert cy.parse_row(row) == {
        "name": "Swiss Admin",
        "link_title": "Link",
        "link_url": "https://github.com/admin-ch",
    }


def test_parse_row_plain_text_has_no_link():
    """A cell without a markdown link yields empty link fields."""
    assert cy.parse_row("Jura|— none known yet\n") == {
        "name": "Jura",
        "link_title": "",
        "link_url": "",
    }


def test_parse_row_strips_surrounding_whitespace():
    assert cy.parse_row("  Foo Bar  |  [T](http://x)  \n")["name"] == "Foo Bar"


def test_parse_row_name_only_when_no_pipe():
    assert cy.parse_row("Solo\n") == {
        "name": "Solo",
        "link_title": "",
        "link_url": "",
    }


# --- convert_to_filename ----------------------------------------------------


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("Zürich Open Data", "zurich_open_data"),
        ("Graubünden", "graubunden"),
        ("CDC-SI", "cdcsi"),
        ("  spaced  ", "spaced"),
        ("Basel-Land", "baselland"),  # punctuation (incl. '-') is stripped, not kept
    ],
)
def test_convert_to_filename(value, expected):
    assert cy.convert_to_filename(value) == expected


# --- read_readme / _extract_table -------------------------------------------


def test_extract_table_missing_marker_raises_clear_error():
    with pytest.raises(ValueError, match="Could not locate table markers"):
        cy._extract_table(
            ["nothing here\n"],
            "|Service|Link|\n",
            "<!-- END FEDERAL LIST -->\n",
        )


def test_real_readme_parses_to_expected_counts():
    fed, canton = cy.read_readme()
    assert len(fed) == 25
    assert len(canton) == 33


# --- create_yaml_files (self-cleaning + idempotent) -------------------------


@pytest.fixture
def sandbox(tmp_path, monkeypatch):
    """Point the generator at a temporary README + data dir."""
    readme = tmp_path / "README.md"
    readme.write_text(MINIMAL_README, encoding="utf-8")
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    monkeypatch.setattr(cy, "README_PATH", readme)
    monkeypatch.setattr(cy, "DATA_DIR", data_dir)
    return data_dir


def _yaml_names(data_dir):
    return sorted(p.name for p in data_dir.glob("*.yaml"))


def test_create_yaml_files_writes_expected_files(sandbox):
    cy.create_yaml_files()
    # _yaml_names returns sorted names; "jura.yaml" is the no-org canton whose
    # filename is the canton name only (empty link_title).
    assert _yaml_names(sandbox) == [
        "aargau_github_org.yaml",
        "admin_swiss_admin.yaml",
        "jura.yaml",
    ]


def test_create_yaml_files_removes_orphans(sandbox):
    (sandbox / "orphan.yaml").write_text("name: stale\n", encoding="utf-8")
    cy.create_yaml_files()
    assert "orphan.yaml" not in _yaml_names(sandbox)


def test_create_yaml_files_is_idempotent(sandbox):
    cy.create_yaml_files()
    first = {p.name: p.read_text(encoding="utf-8") for p in sandbox.glob("*.yaml")}
    cy.create_yaml_files()
    second = {p.name: p.read_text(encoding="utf-8") for p in sandbox.glob("*.yaml")}
    assert first == second
