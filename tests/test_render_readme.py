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

"""Unit + golden tests for the README renderer."""

import pytest

from codeswissgov.models import Organization
from codeswissgov.render.readme import render_readme

SKELETON = (
    "# Title\n\nintro\n\n"
    "<!-- BEGIN FEDERAL LIST -->\n\n|Service|Link|\n|-------|----|\nOLD\n\n"
    "<!-- END FEDERAL LIST -->\n\n"
    "<!-- BEGIN CANTONAL LIST -->\n\n|Canton|Link|\n|------|----|\nOLD\n\n"
    "<!-- END CANTONAL LIST -->\n\n## License\n"
)


def _org(name, authority, handle):
    return Organization(
        name=name, authority=authority, url=f"https://github.com/{handle}"
    )


def test_federal_row_format_and_constant_link_label():
    out = render_readme([_org("Swiss Admin", "federal", "admin-ch")], SKELETON)
    assert "Swiss Admin|[Link](https://github.com/admin-ch)\n" in out


def test_cantonal_row_uses_canton_column_and_unit_label():
    out = render_readme([_org("Statistics I", "canton:ZH", "stat")], SKELETON)
    assert "Zürich|[Statistics I](https://github.com/stat)\n" in out


def test_canton_with_no_org_renders_none_known():
    out = render_readme([_org("Statistics I", "canton:ZH", "stat")], SKELETON)
    # Jura has no org -> derived placeholder row.
    assert "Jura|— none known yet\n" in out


def test_federal_sorted_case_insensitively():
    orgs = [
        _org("Zebra Office", "federal", "z"),
        _org("apple Office", "federal", "a"),
    ]
    out = render_readme(orgs, SKELETON)
    assert out.index("apple Office") < out.index("Zebra Office")


def test_non_table_content_is_untouched():
    out = render_readme([_org("Swiss Admin", "federal", "admin-ch")], SKELETON)
    assert out.startswith("# Title\n\nintro\n\n")
    assert out.endswith("## License\n")


def test_missing_marker_raises_clear_error():
    with pytest.raises(ValueError, match="Could not find markers"):
        render_readme([], "no markers here")


def test_render_is_idempotent():
    orgs = [_org("Swiss Admin", "federal", "admin-ch")]
    once = render_readme(orgs, SKELETON)
    twice = render_readme(orgs, once)
    assert once == twice


# --- golden: committed README.md must match a fresh render of data/orgs -------


def test_committed_readme_matches_render(repo_root, organizations):
    rendered = render_readme(
        organizations, (repo_root / "README.md").read_text(encoding="utf-8")
    )
    assert rendered == (repo_root / "README.md").read_text(
        encoding="utf-8"
    ), "README.md is out of sync with data/orgs — run `python -m codeswissgov build`."
