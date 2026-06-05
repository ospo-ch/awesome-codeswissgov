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

"""Unit tests for the Organization and Repository models."""

import pytest
from pydantic import ValidationError

from codeswissgov.models import Organization, Repository


def test_valid_federal_org():
    org = Organization(
        name="Federal Chancellery",
        authority="federal",
        url="https://github.com/swiss",
    )
    assert org.is_federal
    assert org.canton_code is None
    assert org.official is False
    assert org.provenance is None


def test_valid_cantonal_org():
    org = Organization(
        name="Statistics I",
        authority="canton:ZH",
        url="https://github.com/statistikstadtzuerich",
    )
    assert not org.is_federal
    assert org.canton_code == "ZH"


def test_url_is_required():
    # Cantons with no org are not records; every stored org has a url.
    with pytest.raises(ValidationError):
        Organization(name="Jura", authority="canton:JU")


def test_name_is_stripped():
    url = "https://github.com/kanton-bern"
    assert Organization(name="  Bern  ", authority="canton:BE", url=url).name == "Bern"


def test_empty_name_rejected():
    with pytest.raises(ValidationError, match="name must not be empty"):
        Organization(name="   ", authority="canton:BE", url="https://github.com/x")


@pytest.mark.parametrize("authority", ["municipal", "canton:XX", "canton:", "FEDERAL"])
def test_bad_authority_rejected(authority):
    with pytest.raises(ValidationError):
        Organization(name="X", authority=authority, url="https://github.com/x")


def test_non_github_url_rejected():
    with pytest.raises(ValidationError, match="github.com"):
        Organization(name="X", authority="canton:ZH", url="https://gitlab.com/x")


def test_official_requires_provenance():
    with pytest.raises(ValidationError, match="requires non-empty provenance"):
        Organization(
            name="X", authority="federal", url="https://github.com/x", official=True
        )


def test_official_with_provenance_is_valid():
    org = Organization(
        name="X",
        authority="federal",
        url="https://github.com/x",
        official=True,
        provenance="verified-domain: x.admin.ch",
    )
    assert org.official is True


def test_unknown_field_rejected():
    with pytest.raises(ValidationError):
        Organization(
            name="X",
            authority="canton:ZH",
            url="https://github.com/x",
            link_title="legacy field",
        )


def test_repository_defaults():
    repo = Repository(name="tool", url="https://github.com/swiss/tool")
    assert repo.license is None
    assert repo.language is None
    assert repo.topics == []
    assert repo.archived is False
    assert repo.last_activity is None
    assert repo.has_publiccode_yml is False
    assert repo.has_security_md is False


def test_repository_full_record():
    repo = Repository(
        name="tool",
        url="https://github.com/swiss/tool",
        license="MIT",
        language="Python",
        topics=["gov", "ch"],
        archived=True,
        last_activity="2026-01-15",
        has_publiccode_yml=True,
        has_security_md=True,
    )
    assert repo.license == "MIT"
    assert repo.topics == ["gov", "ch"]
    assert repo.archived is True


def test_repository_missing_license_is_compliance_flag():
    assert Repository(name="t", url="https://github.com/o/t").is_compliance_flag
    licensed = Repository(name="t", url="https://github.com/o/t", license="Apache-2.0")
    assert not licensed.is_compliance_flag


def test_repository_name_is_stripped():
    repo = Repository(name="  tool  ", url="https://github.com/o/tool")
    assert repo.name == "tool"


def test_repository_empty_name_rejected():
    with pytest.raises(ValidationError, match="name must not be empty"):
        Repository(name="   ", url="https://github.com/o/t")


def test_repository_non_github_url_rejected():
    with pytest.raises(ValidationError, match="github.com"):
        Repository(name="t", url="https://gitlab.com/o/t")


def test_repository_unknown_field_rejected():
    with pytest.raises(ValidationError):
        Repository(name="t", url="https://github.com/o/t", stars=5)
