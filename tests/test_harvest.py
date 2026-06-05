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

"""Tests for harvest orchestration (offline; injected client)."""

import json

import pytest

from codeswissgov.harvest import org_login, run_harvest
from codeswissgov.harvest.github import GitHubError
from codeswissgov.models import Repository


class FakeGitHub:
    """Stand-in for GitHubClient: returns canned repos, errors on listed logins."""

    def __init__(self, repos_by_login, errors=()):
        self.repos_by_login = repos_by_login
        self.errors = set(errors)
        self.calls = []

    def fetch_org_repositories(self, login):
        self.calls.append(login)
        if login in self.errors:
            raise GitHubError(f"boom: {login}")
        return self.repos_by_login.get(login, [])


def _repo(handle, name, **kw):
    return Repository(name=name, url=f"https://github.com/{handle}/{name}", **kw)


def _make_root(tmp_path, orgs):
    """Scaffold a repo root with data/orgs/*.yaml (federal) for given handles."""
    orgs_dir = tmp_path / "data" / "orgs"
    orgs_dir.mkdir(parents=True)
    for handle in orgs:
        (orgs_dir / f"{handle}.yaml").write_text(
            f"name: {handle}\nauthority: federal\nurl: https://github.com/{handle}\n"
        )
    return tmp_path


def _inventory(root):
    return json.loads((root / "inventory.json").read_text(encoding="utf-8"))


def test_harvest_writes_repos_and_timestamp(tmp_path):
    root = _make_root(tmp_path, ["admin-ch", "swiss"])
    github = FakeGitHub(
        {
            "admin-ch": [_repo("admin-ch", "tool", license="MIT")],
            "swiss": [_repo("swiss", "index"), _repo("swiss", "site")],
        }
    )
    summary = run_harvest("t", root, github=github, now="2026-06-05T00:00:00Z")

    assert summary.orgs_total == 2
    assert summary.orgs_refreshed == 2
    assert summary.repos_total == 3
    assert summary.orgs_failed == []

    by_url = {o["url"]: o for o in _inventory(root)["organizations"]}
    admin = by_url["https://github.com/admin-ch"]
    assert admin["harvested_at"] == "2026-06-05T00:00:00Z"
    assert [r["name"] for r in admin["repositories"]] == ["tool"]
    assert admin["repositories"][0]["license"] == "MIT"
    assert len(by_url["https://github.com/swiss"]["repositories"]) == 2


def test_harvest_keeps_cached_data_on_failure(tmp_path):
    root = _make_root(tmp_path, ["admin-ch", "swiss"])
    # First, successful run populates both.
    github = FakeGitHub(
        {
            "admin-ch": [_repo("admin-ch", "tool")],
            "swiss": [_repo("swiss", "index")],
        }
    )
    run_harvest("t", root, github=github, now="2026-01-01T00:00:00Z")

    # Second run: admin-ch fails, swiss refreshes with a new repo set.
    github2 = FakeGitHub(
        {"swiss": [_repo("swiss", "index"), _repo("swiss", "new")]},
        errors=["admin-ch"],
    )
    summary = run_harvest("t", root, github=github2, now="2026-02-02T00:00:00Z")

    assert summary.orgs_failed == ["admin-ch"]
    assert summary.orgs_refreshed == 1

    by_url = {o["url"]: o for o in _inventory(root)["organizations"]}
    admin = by_url["https://github.com/admin-ch"]
    swiss = by_url["https://github.com/swiss"]
    # admin-ch retains the prior snapshot verbatim (cache fallback).
    assert admin["harvested_at"] == "2026-01-01T00:00:00Z"
    assert [r["name"] for r in admin["repositories"]] == ["tool"]
    # swiss got the fresh data + new timestamp.
    assert swiss["harvested_at"] == "2026-02-02T00:00:00Z"
    assert [r["name"] for r in swiss["repositories"]] == ["index", "new"]


def test_harvest_first_failure_leaves_org_empty(tmp_path):
    root = _make_root(tmp_path, ["admin-ch"])
    github = FakeGitHub({}, errors=["admin-ch"])
    summary = run_harvest("t", root, github=github, now="2026-06-05T00:00:00Z")

    assert summary.orgs_failed == ["admin-ch"]
    assert summary.repos_total == 0
    org = _inventory(root)["organizations"][0]
    assert org["repositories"] == []
    assert org["harvested_at"] is None


@pytest.mark.parametrize(
    "url,expected",
    [
        ("https://github.com/admin-ch", "admin-ch"),
        ("https://github.com/cdc-si/", "cdc-si"),
        ("https://github.com/KOST-CECO", "KOST-CECO"),
    ],
)
def test_org_login(url, expected):
    assert org_login(url) == expected
