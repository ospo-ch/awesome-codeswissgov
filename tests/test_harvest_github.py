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

"""Offline tests for the GitHub GraphQL client (recorded fixtures only)."""

import json
from pathlib import Path

import httpx
import pytest

from codeswissgov.harvest.github import GitHubClient, GitHubError

FIXTURES = Path(__file__).resolve().parent / "fixtures"


def _fixture(name: str) -> dict:
    return json.loads((FIXTURES / f"{name}.json").read_text(encoding="utf-8"))


def _client() -> GitHubClient:
    return GitHubClient(token="t0ken", client=httpx.Client())


def test_fetch_single_page_maps_all_fields(httpx_mock):
    httpx_mock.add_response(json=_fixture("graphql_org_single"))
    repos = _client().fetch_org_repositories("admin-ch")

    assert [r.name for r in repos] == ["open-tool", "legacy-archive"]

    full = repos[0]
    assert full.url == "https://github.com/admin-ch/open-tool"
    assert full.license == "MIT"
    assert full.language == "Python"
    assert full.topics == ["government", "switzerland"]
    assert full.archived is False
    assert full.last_activity == "2026-01-15"  # date only, time dropped
    assert full.has_publiccode_yml is True
    assert full.has_security_md is True

    bare = repos[1]
    assert bare.license is None and bare.is_compliance_flag
    assert bare.language is None
    assert bare.topics == []
    assert bare.archived is True
    assert bare.last_activity is None
    assert bare.has_publiccode_yml is False
    assert bare.has_security_md is False


def test_pagination_follows_cursor(httpx_mock):
    httpx_mock.add_response(json=_fixture("graphql_org_page1"))
    httpx_mock.add_response(json=_fixture("graphql_org_page2"))

    repos = _client().fetch_org_repositories("admin-ch")
    assert [r.name for r in repos] == ["alpha", "beta"]

    requests = httpx_mock.get_requests()
    assert len(requests) == 2
    first = json.loads(requests[0].read())
    second = json.loads(requests[1].read())
    assert first["variables"]["cursor"] is None
    assert second["variables"]["cursor"] == "Y3Vyc29yOjE="  # page1 endCursor


def test_sends_bearer_token(httpx_mock):
    httpx_mock.add_response(json=_fixture("graphql_org_single"))
    _client().fetch_org_repositories("admin-ch")
    assert httpx_mock.get_requests()[0].headers["Authorization"] == "bearer t0ken"


def test_unknown_org_raises(httpx_mock):
    httpx_mock.add_response(json=_fixture("graphql_org_not_found"))
    with pytest.raises(GitHubError, match="not found"):
        _client().fetch_org_repositories("nope")


def test_graphql_errors_raise(httpx_mock):
    httpx_mock.add_response(json={"errors": [{"message": "Bad credentials"}]})
    with pytest.raises(GitHubError, match="GraphQL errors"):
        _client().fetch_org_repositories("admin-ch")


def test_http_status_error_raises(httpx_mock):
    httpx_mock.add_response(status_code=401, json={"message": "Unauthorized"})
    with pytest.raises(GitHubError, match="request failed"):
        _client().fetch_org_repositories("admin-ch")
