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

"""Tests for link-rot classification, rendering, and offline orchestration."""

import httpx

from codeswissgov.check import run_check
from codeswissgov.check.linkrot import (
    ALIVE,
    ERROR,
    GONE,
    RENAMED,
    LinkResult,
    build_report,
    classify,
    render_report,
)
from codeswissgov.models import Organization


def _org(url: str = "https://github.com/admin-ch", name: str = "Org") -> Organization:
    return Organization(name=name, authority="federal", url=url)


# --- classify ---------------------------------------------------------------


def test_classify_200_is_alive():
    result = classify(_org(), 200, None)
    assert result.state == ALIVE and result.detail is None


def test_classify_redirect_to_same_login_is_alive():
    # Trailing-slash / case normalization redirects to the same org, not a move.
    org = _org("https://github.com/cdc-si/")
    result = classify(org, 301, "https://github.com/CDC-SI")
    assert result.state == ALIVE


def test_classify_redirect_to_new_login_is_renamed():
    org = _org("https://github.com/old-name")
    result = classify(org, 301, "https://github.com/new-name")
    assert result.state == RENAMED
    assert result.detail == "https://github.com/new-name"


def test_classify_redirect_without_location_is_error():
    result = classify(_org(), 302, None)
    assert result.state == ERROR
    assert "without Location" in result.detail


def test_classify_404_is_gone():
    assert classify(_org(), 404, None).state == GONE


def test_classify_unexpected_status_is_error():
    result = classify(_org(), 503, None)
    assert result.state == ERROR
    assert "503" in result.detail


# --- build_report / render_report -------------------------------------------


def _results() -> list[LinkResult]:
    return [
        LinkResult(_org("https://github.com/a", "Alive Org"), ALIVE),
        LinkResult(
            _org("https://github.com/old", "Moved Org"),
            RENAMED,
            "https://github.com/new",
        ),
        LinkResult(_org("https://github.com/dead", "Dead Org"), GONE),
        LinkResult(_org("https://github.com/oops", "Flaky Org"), ERROR, "timed out"),
    ]


def test_build_report_groups_by_state():
    report = build_report(_results())
    assert report.checked == 4
    assert [r.org.name for r in report.renamed] == ["Moved Org"]
    assert [r.org.name for r in report.gone] == ["Dead Org"]
    assert [r.org.name for r in report.errors] == ["Flaky Org"]


def test_render_report_lists_actions_and_counts():
    text = render_report(build_report(_results()))

    assert text.endswith("\n")
    assert "Checked 4 org URL(s)" in text
    assert "data/orgs is never edited" in text
    assert "- 1 alive" in text
    assert "Moved Org: https://github.com/old → https://github.com/new" in text
    assert "Dead Org: https://github.com/dead" in text
    assert "Flaky Org: https://github.com/oops (timed out)" in text


def test_render_report_shows_none_and_omits_error_section_when_clean():
    text = render_report(build_report([LinkResult(_org(), ALIVE)]))
    assert "## Renamed" in text and "## Gone" in text
    assert "- (none)" in text
    # No errors -> the "could not be checked" section is omitted entirely.
    assert "## Could not be checked" not in text


# --- run_check (offline via pytest-httpx) ------------------------------------


def _root(tmp_path, handles):
    orgs_dir = tmp_path / "data" / "orgs"
    orgs_dir.mkdir(parents=True)
    for handle in handles:
        (orgs_dir / f"{handle}.yaml").write_text(
            f"name: {handle}\nauthority: federal\nurl: https://github.com/{handle}\n"
        )
    return tmp_path


def test_run_check_classifies_each_org_offline(tmp_path, httpx_mock):
    root = _root(tmp_path, ["alive-org", "moved-org", "dead-org"])
    httpx_mock.add_response(url="https://github.com/alive-org", status_code=200)
    httpx_mock.add_response(
        url="https://github.com/moved-org",
        status_code=301,
        headers={"Location": "https://github.com/renamed-org"},
    )
    httpx_mock.add_response(url="https://github.com/dead-org", status_code=404)

    report = run_check(root, client=httpx.Client())

    assert report.checked == 3
    assert [r.org.name for r in report.alive] == ["alive-org"]
    assert [r.detail for r in report.renamed] == ["https://github.com/renamed-org"]
    assert [r.org.name for r in report.gone] == ["dead-org"]


def test_run_check_records_transport_error_without_aborting(tmp_path, httpx_mock):
    root = _root(tmp_path, ["ok-org", "boom-org"])
    httpx_mock.add_response(url="https://github.com/ok-org", status_code=200)
    httpx_mock.add_exception(
        httpx.ConnectTimeout("slow"), url="https://github.com/boom-org"
    )

    report = run_check(root, client=httpx.Client())

    assert [r.org.name for r in report.alive] == ["ok-org"]
    assert [r.org.name for r in report.errors] == ["boom-org"]
