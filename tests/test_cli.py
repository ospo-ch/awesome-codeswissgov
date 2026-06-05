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

"""Tests for the build/validate CLI and the build helpers."""

import shutil

import pytest

from codeswissgov import __main__ as cli
from codeswissgov.build import build, render_all, validate


@pytest.fixture
def tmp_repo(tmp_path, repo_root):
    """A throwaway repo with data/orgs + README copied from the real tree."""
    (tmp_path / "data").mkdir()
    shutil.copytree(repo_root / "data" / "orgs", tmp_path / "data" / "orgs")
    shutil.copy(repo_root / "README.md", tmp_path / "README.md")
    return tmp_path


# --- build helper -----------------------------------------------------------


def test_build_writes_both_views_and_is_idempotent(tmp_repo):
    assert not (tmp_repo / "inventory.json").exists()
    build(tmp_repo)
    assert (tmp_repo / "inventory.json").exists()
    first = (
        (tmp_repo / "README.md").read_text(),
        (tmp_repo / "inventory.json").read_text(),
    )
    build(tmp_repo)
    second = (
        (tmp_repo / "README.md").read_text(),
        (tmp_repo / "inventory.json").read_text(),
    )
    assert first == second


def test_validate_passes_after_build(tmp_repo):
    build(tmp_repo)
    assert validate(tmp_repo) == []


def test_validate_flags_stale_readme(tmp_repo):
    build(tmp_repo)
    # Add a new org file without rebuilding -> README + inventory now stale.
    (tmp_repo / "data" / "orgs" / "neworg.yaml").write_text(
        "name: New Office\nauthority: federal\nurl: https://github.com/new\n"
    )
    stale = validate(tmp_repo)
    assert "README.md" in stale
    assert "inventory.json" in stale


def test_validate_raises_on_invalid_schema(tmp_repo):
    (tmp_repo / "data" / "orgs" / "bad.yaml").write_text(
        "name: Bad\nauthority: municipal\nurl: https://github.com/bad\n"
    )
    with pytest.raises(ValueError, match="bad.yaml"):
        render_all(tmp_repo)


# --- CLI dispatch -----------------------------------------------------------


def test_cli_validate_on_committed_repo_succeeds():
    # The committed tree must always be in sync (this is also the CI gate).
    assert cli.main(["validate"]) == 0


def test_cli_help_returns_zero(capsys):
    assert cli.main(["--help"]) == 0
    assert "build" in capsys.readouterr().out


def test_cli_no_command_is_usage_error(capsys):
    assert cli.main([]) == 2
    assert "usage" in capsys.readouterr().err


def test_cli_unknown_command_is_usage_error():
    assert cli.main(["frobnicate"]) == 2


# --- harvest command --------------------------------------------------------


def test_harvest_requires_a_token(monkeypatch, capsys):
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    assert cli.main(["harvest"]) == 2
    assert "token is required" in capsys.readouterr().err


@pytest.mark.parametrize(
    "argv,env,expected",
    [
        (["harvest", "--token", "flag-tok"], None, "flag-tok"),
        (["harvest", "--token=eq-tok"], None, "eq-tok"),
        (["harvest"], "env-tok", "env-tok"),
        (["harvest", "--token", "flag-wins"], "env-tok", "flag-wins"),
    ],
)
def test_harvest_token_resolution(monkeypatch, argv, env, expected):
    if env is None:
        monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    else:
        monkeypatch.setenv("GITHUB_TOKEN", env)
    seen = {}

    def fake_run_harvest(token):
        seen["token"] = token
        return _summary(refreshed=1)

    monkeypatch.setattr(cli, "run_harvest", fake_run_harvest)
    assert cli.main(argv) == 0
    assert seen["token"] == expected


def test_harvest_reports_failures_but_succeeds(monkeypatch, capsys):
    monkeypatch.setattr(
        cli, "run_harvest", lambda token: _summary(refreshed=3, failed=["x"])
    )
    assert cli.main(["harvest", "--token", "t"]) == 0
    err = capsys.readouterr().err
    assert "kept cached data" in err


def test_harvest_returns_nonzero_when_nothing_refreshed(monkeypatch):
    monkeypatch.setattr(
        cli, "run_harvest", lambda token: _summary(refreshed=0, failed=["x", "y"])
    )
    assert cli.main(["harvest", "--token", "t"]) == 1


def _summary(*, refreshed, failed=None):
    from codeswissgov.harvest import HarvestSummary

    failed = failed or []
    return HarvestSummary(
        orgs_total=refreshed + len(failed),
        orgs_refreshed=refreshed,
        repos_total=refreshed,
        orgs_failed=failed,
    )
