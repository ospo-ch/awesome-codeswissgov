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

"""Unit tests for the Organization model."""

import pytest
from pydantic import ValidationError

from codeswissgov.models import Organization


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


def test_cantonal_org_without_url_is_a_known_gap():
    org = Organization(name="Jura", authority="canton:JU", url=None)
    assert org.url is None
    assert org.canton_code == "JU"


def test_name_is_stripped():
    assert Organization(name="  Bern  ", authority="canton:BE", url=None).name == "Bern"


def test_empty_name_rejected():
    with pytest.raises(ValidationError, match="name must not be empty"):
        Organization(name="   ", authority="canton:BE", url=None)


@pytest.mark.parametrize("authority", ["municipal", "canton:XX", "canton:", "FEDERAL"])
def test_bad_authority_rejected(authority):
    with pytest.raises(ValidationError):
        Organization(name="X", authority=authority, url=None)


def test_non_github_url_rejected():
    with pytest.raises(ValidationError, match="github.com"):
        Organization(name="X", authority="canton:ZH", url="https://gitlab.com/x")


def test_federal_org_requires_url():
    with pytest.raises(ValidationError, match="federal organization must have a url"):
        Organization(name="X", authority="federal", url=None)


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
            name="X", authority="canton:ZH", url=None, link_title="legacy field"
        )
