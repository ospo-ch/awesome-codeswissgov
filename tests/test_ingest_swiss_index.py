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

"""Offline tests for the swiss/index source (recorded fixture only)."""

from pathlib import Path

import httpx
import pytest

from codeswissgov.ingest.registry import CANTONAL_HINT, FEDERAL_HINT, IngestError
from codeswissgov.ingest.swiss_index import (
    SwissIndexSource,
    fetch_readme,
    parse_index,
)

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "swiss_index_readme.md"


def _readme() -> str:
    return FIXTURE.read_text(encoding="utf-8")


def test_parse_extracts_github_orgs_and_skips_other_forges():
    result = parse_index(_readme())

    assert [c.url for c in result.candidates] == [
        "https://github.com/admin-ch",
        "https://github.com/cdc-si/",
        "https://github.com/KOST-CECO",
        "https://github.com/govcert-ch",
        "https://github.com/visualize-admin",
        "https://github.com/swisscovid",
        "https://github.com/DCC-BS",
    ]
    # GitLab + self-hosted GitLab are out of scope, recorded transparently.
    assert result.skipped == [
        "https://gitlab.com/swiss-armed-forces",
        "https://gitlabext.wsl.ch/safe",
    ]


def test_parse_classifies_authority_hint_by_section():
    by_url = {c.url: c for c in parse_index(_readme()).candidates}

    # Both "Federal Ownership" and "Federal Projects" sections -> federal.
    assert by_url["https://github.com/admin-ch"].authority_hint == FEDERAL_HINT
    assert by_url["https://github.com/swisscovid"].authority_hint == FEDERAL_HINT
    # The cantonal section -> cantonal.
    assert by_url["https://github.com/DCC-BS"].authority_hint == CANTONAL_HINT


def test_parse_records_section_and_source_as_provenance():
    by_url = {c.url: c for c in parse_index(_readme()).candidates}
    govcert = by_url["https://github.com/govcert-ch"]

    assert govcert.source == "swiss/index"
    assert "Federal Ownership" in govcert.section
    assert parse_index(_readme()).name == "swiss/index"


def test_fetch_readme_returns_body(httpx_mock):
    httpx_mock.add_response(text="# index\n* https://github.com/admin-ch\n")
    body = fetch_readme(httpx.Client(), url="https://example.test/README.md")
    assert "github.com/admin-ch" in body


def test_fetch_readme_raises_on_http_error(httpx_mock):
    httpx_mock.add_response(status_code=404)
    with pytest.raises(IngestError, match="failed to fetch"):
        fetch_readme(httpx.Client(), url="https://example.test/missing.md")


def test_source_fetch_end_to_end(httpx_mock):
    httpx_mock.add_response(text=_readme())
    result = SwissIndexSource(url="https://example.test/README.md").fetch(
        httpx.Client()
    )

    assert result.name == "swiss/index"
    assert len(result.candidates) == 7
    assert len(result.skipped) == 2
